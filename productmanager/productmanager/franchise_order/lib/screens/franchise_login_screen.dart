import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

class FranchiseLoginScreen extends StatefulWidget {
  const FranchiseLoginScreen({super.key});

  @override
  State<FranchiseLoginScreen> createState() => _FranchiseLoginScreenState();
}

class _FranchiseLoginScreenState extends State<FranchiseLoginScreen> {
  final _clientIdController = TextEditingController();
  final _bizNumController = TextEditingController();
  final _pwController = TextEditingController();

  bool _isLoading = false;
  bool _isPwVisible = false;
  bool _rememberInfo = false;
  bool _autoLogin = false;

  @override
  void initState() {
    super.initState();
    _loadSavedLoginInfo();
  }

  Future<void> _loadSavedLoginInfo() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _rememberInfo = prefs.getBool('remember') ?? false;
      _autoLogin = prefs.getBool('auto_login') ?? false;

      if (_rememberInfo || _autoLogin) {
        _clientIdController.text = prefs.getString('client_id') ?? '';
        _bizNumController.text = prefs.getString('biz_number') ?? '';
        _pwController.text = prefs.getString('password') ?? '';
      }
    });

    if (_autoLogin) {
      _login();
    }
  }

  Future<void> _saveLoginPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('remember', _rememberInfo);
    await prefs.setBool('auto_login', _autoLogin);

    if (_rememberInfo || _autoLogin) {
      await prefs.setString('client_id', _clientIdController.text.trim());
      await prefs.setString('biz_number', _bizNumController.text.trim());
      await prefs.setString('password', _pwController.text.trim());
    } else {
      await prefs.remove('client_id');
      await prefs.remove('biz_number');
      await prefs.remove('password');
    }
  }

  void _login() async {
    final clientId = _clientIdController.text.trim();
    final businessNumber = _bizNumController.text.trim();
    final pw = _pwController.text.trim();

    if (clientId.isEmpty || businessNumber.isEmpty || pw.isEmpty) {
      _showError("거래처번호, 사업자번호, 비밀번호를 모두 입력해주세요.");
      return;
    }

    setState(() => _isLoading = true);

    try {
      final response = await ApiService.franchiseLogin(
        int.parse(clientId),
        businessNumber,
        pw,
      );

      if (response != null) {
        await _saveLoginPrefs(); // ✅ 로그인 성공 후 저장
        Provider.of<AuthProvider>(context, listen: false).setClientData(
          clientId: response['client_id'],
          clientName: response['client_name'],
          token: response['token'] ?? '',
        );
        Navigator.pushReplacementNamed(context, '/select_date');
      } else {
        throw Exception("로그인 실패");
      }
    } catch (e) {
      _showError("로그인 실패: ${e.toString()}");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, textAlign: TextAlign.center),
        backgroundColor: Colors.redAccent,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeColor = Colors.indigo;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: Center(
        child: Card(
          elevation: 8,
          margin: const EdgeInsets.symmetric(horizontal: 24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 560),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text("🍦 성심유통 IceCream", style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold, color: themeColor)),
                    const SizedBox(height: 8),
                    Text("점주 로그인", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.black87)),
                    const SizedBox(height: 24),
                    _buildInputField(_clientIdController, "거래처 번호", TextInputType.number),
                    const SizedBox(height: 16),
                    _buildInputField(_bizNumController, "사업자번호", TextInputType.text),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _pwController,
                      obscureText: !_isPwVisible,
                      decoration: InputDecoration(
                        labelText: "비밀번호",
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          icon: Icon(_isPwVisible ? Icons.visibility : Icons.visibility_off),
                          onPressed: () => setState(() => _isPwVisible = !_isPwVisible),
                        ),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Checkbox(
                          value: _rememberInfo,
                          onChanged: (val) => setState(() => _rememberInfo = val!),
                        ),
                        const Text("정보 기억하기"),
                        const SizedBox(width: 20),
                        Checkbox(
                          value: _autoLogin,
                          onChanged: (val) => setState(() => _autoLogin = val!),
                        ),
                        const Text("자동 로그인"),
                      ],
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _login,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: themeColor,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: _isLoading
                            ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                            : const Text("로그인", style: TextStyle(fontSize: 16)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInputField(TextEditingController controller, String label, TextInputType type) {
    return TextField(
      controller: controller,
      keyboardType: type,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import 'home_screen.dart';
import 'package:provider/provider.dart';
import '../auth_provider.dart';
import '../user.dart';
import '../product_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _idController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;
  bool _rememberMe = false;
  bool _autoLogin = false;

  @override
  void initState() {
    super.initState();
    _loadSavedLogin();
  }

  // ✅ 저장된 로그인 정보 불러오기
  Future<void> _loadSavedLogin() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _idController.text = prefs.getString('saved_id') ?? '';
      _passwordController.text = prefs.getString('saved_password') ?? '';
      _rememberMe = prefs.getBool('remember_me') ?? false;
      _autoLogin = prefs.getBool('auto_login') ?? false;
    });

    // ✅ 자동 로그인이 체크되어 있으면 로그인 시도
    if (_autoLogin && _idController.text.isNotEmpty && _passwordController.text.isNotEmpty) {
      _login();
    }
  }

  // ✅ 로그인 정보 저장
  Future<void> _saveLoginData() async {
    final prefs = await SharedPreferences.getInstance();
    if (_rememberMe) {
      await prefs.setString('saved_id', _idController.text);
      await prefs.setString('saved_password', _passwordController.text);
    } else {
      await prefs.remove('saved_id');
      await prefs.remove('saved_password');
    }
    await prefs.setBool('remember_me', _rememberMe);
    await prefs.setBool('auto_login', _autoLogin);
  }

  Future<void> _login() async {
    final idText = _idController.text.trim();
    final password = _passwordController.text;

    if (idText.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = "사원ID와 비밀번호를 입력하세요.");
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final id = int.parse(idText);

      final response = await ApiService.login(id, password);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['token'];

        if (token == null) {
          setState(() => _errorMessage = "응답에 token이 없습니다.");
        } else {
          final user = User(
            id: data["id"],
            name: data["name"],
            role: data["role"],
            token: data["token"],
          );

          context.read<AuthProvider>().setUser(user);
          final productData = await ApiService.fetchAllProducts(token);
          context.read<ProductProvider>().setProducts(productData);

          // ✅ 로그인 정보 저장
          await _saveLoginData();

          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => HomeScreen(token: token)),
          );
        }
      } else {
        setState(() {
          _errorMessage = "로그인 실패: ${response.statusCode}\n${response.body}";
        });
      }
    } catch (e) {
      setState(() => _errorMessage = "로그인 오류: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          Positioned.fill(
            child: Image.asset(
              'assets/login.png',
              fit: BoxFit.cover,
            ),
          ),
          Center(
            child: Container(
              width: 300,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.9),
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black26,
                    blurRadius: 6,
                    offset: Offset(0, 3),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: _idController,
                    decoration: InputDecoration(
                      labelText: "사원 ID",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      prefixIcon: Icon(Icons.person),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _passwordController,
                    decoration: InputDecoration(
                      labelText: "비밀번호",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      prefixIcon: Icon(Icons.lock),
                    ),
                    obscureText: true,
                  ),
                  Row(
                    children: [
                      Checkbox(
                        value: _rememberMe,
                        onChanged: (value) {
                          setState(() {
                            _rememberMe = value!;
                          });
                        },
                      ),
                      const Text("아이디 저장"),
                      Spacer(),
                      Checkbox(
                        value: _autoLogin,
                        onChanged: (value) {
                          setState(() {
                            _autoLogin = value!;
                          });
                        },
                      ),
                      const Text("자동 로그인"),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _isLoading
                      ? const CircularProgressIndicator()
                      : ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    onPressed: _login,
                    child: const Text("로그인"),
                  ),
                  if (_errorMessage != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(
                        _errorMessage!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

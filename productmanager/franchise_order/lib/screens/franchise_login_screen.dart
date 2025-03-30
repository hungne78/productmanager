import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
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

  void _login() async {
    final clientId = _clientIdController.text.trim();
    final businessNumber = _bizNumController.text.trim();
    final pw = _pwController.text.trim();

    if (clientId.isEmpty || businessNumber.isEmpty || pw.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("거래처번호, 사업자번호, 비밀번호를 모두 입력해주세요.")),
      );
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
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("로그인 실패: ${e.toString()}")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("점주 로그인")),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _clientIdController,
              decoration: const InputDecoration(labelText: "거래처 번호"),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: _bizNumController,
              decoration: const InputDecoration(labelText: "사업자번호"),
              keyboardType: TextInputType.text,
            ),
            TextField(
              controller: _pwController,
              decoration: const InputDecoration(labelText: "비밀번호"),
              obscureText: true,
            ),
            const SizedBox(height: 24),
            _isLoading
                ? const CircularProgressIndicator()
                : ElevatedButton(
              onPressed: _login,
              child: const Text("로그인"),
            ),
          ],
        ),
      ),
    );
  }
}

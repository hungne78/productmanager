import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../services/api_service.dart';
import 'home_screen.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';  // AuthProvider import
import '../user.dart';        // User model
import '../product_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _idController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  String? _errorMessage;

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

      // ApiService.login 호출
      final response = await ApiService.login(id, password);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final token = data['token'];

        if (token == null) {
          setState(() => _errorMessage = "응답에 token이 없습니다.");
        } else {

          // User 객체 생성
          final user = User(
            id: data["id"],    // <-- data["id"]
            name: data["name"],
            role: data["role"],
            token: data["token"],
          );
          // Provider를 통해 user 저장
          context.read<AuthProvider>().setUser(user);
          // 홈화면으로 이동
          // **상품 데이터 불러오기**
          final productResponse = await ApiService.fetchAllProducts(token);
          if (productResponse.statusCode == 200) {
            final productData = jsonDecode(productResponse.body);
            context.read<ProductProvider>().setProducts(productData);
          }
          // 로그인 성공 → 홈화면 이동
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
      appBar: AppBar(
        title: const Text("로그인"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _idController,
              decoration: const InputDecoration(labelText: "사원 ID"),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: "비밀번호"),
              obscureText: true,
            ),
            const SizedBox(height: 16),
            _isLoading
                ? const CircularProgressIndicator()
                : ElevatedButton(
              onPressed: _login,
              child: const Text("로그인"),
            ),
            if (_errorMessage != null)
              Text(
                _errorMessage!,
                style: const TextStyle(color: Colors.red),
              )
          ],
        ),
      ),
    );
  }
}

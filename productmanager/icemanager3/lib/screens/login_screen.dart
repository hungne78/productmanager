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
          // ✅ 배경 이미지 (화면에 꽉 차게)
          Positioned.fill(
            child: Image.asset(
              'assets/login.png',  // assets 폴더에 login.png 추가 필요
              fit: BoxFit.cover,  // ✅ 이미지를 화면에 꽉 차게
            ),
          ),

          // ✅ 로그인 입력창을 화면 중앙에 배치
          Center(
            child: Container(
              width: 300, // 로그인 박스의 너비 조절
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.9), // ✅ 반투명한 흰색 배경
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

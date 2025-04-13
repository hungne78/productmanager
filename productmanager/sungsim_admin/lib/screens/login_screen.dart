// lib/screens/login_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/auth_provider.dart';
import 'admin_home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _pwController = TextEditingController();
  bool _autoLogin = false;

  @override
  void initState() {
    super.initState();
    _loadSavedCredentials();
  }

  Future<void> _loadSavedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final savedEmail = prefs.getString("saved_email") ?? '';
    final savedPassword = prefs.getString("saved_password") ?? '';
    final autoLogin = prefs.getBool("auto_login") ?? false;

    setState(() {
      _emailController.text = savedEmail;
      _pwController.text = savedPassword;
      _autoLogin = autoLogin;
    });

    if (autoLogin && savedEmail.isNotEmpty && savedPassword.isNotEmpty) {
      _attemptLogin(savedEmail, savedPassword);
    }
  }

  Future<void> _attemptLogin(String email, String password) async {
    final auth = context.read<AuthProvider>();
    await auth.login(email, password);
    if (auth.isLoggedIn) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const AdminHomeScreen()),
      );
    } else if (auth.error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(auth.error!)),
      );
    }
  }

  Future<void> _saveCredentials(String email, String password, bool autoLogin) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString("saved_email", email);
    await prefs.setString("saved_password", password);
    await prefs.setBool("auto_login", autoLogin);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text("관리자 로그인"),
        centerTitle: true,
      ),
      body: Center(
        child: Card(
          elevation: 8,
          margin: const EdgeInsets.all(24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.lock_outline, size: 48, color: Colors.indigo),
                const SizedBox(height: 16),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                    labelText: "이메일",
                    prefixIcon: Icon(Icons.email_outlined),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _pwController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: "비밀번호",
                    prefixIcon: Icon(Icons.lock),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Checkbox(
                      value: _autoLogin,
                      onChanged: (val) {
                        setState(() {
                          _autoLogin = val ?? false;
                        });
                      },
                    ),
                    const Text("자동 로그인"),
                    const Spacer(),
                    TextButton(
                      onPressed: () {
                        _emailController.clear();
                        _pwController.clear();
                      },
                      child: const Text("지우기"),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                auth.isLoading
                    ? const CircularProgressIndicator()
                    : SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.login),
                    label: const Text("로그인"),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      backgroundColor: Colors.indigo,
                    ),
                    onPressed: () async {
                      final email = _emailController.text.trim();
                      final password = _pwController.text.trim();

                      await _saveCredentials(email, password, _autoLogin);
                      await _attemptLogin(email, password);
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

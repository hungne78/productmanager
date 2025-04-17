// lib/providers/auth_provider.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class AuthProvider extends ChangeNotifier {
  String? _token;      // JWT 등
  Map<String, dynamic>? _adminUser; // 로그인된 관리자 정보
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _user;
  Map<String, dynamic>? get user => _user;
  String? get token => _token;
  Map<String, dynamic>? get adminUser => _adminUser;
  bool get isLoading => _isLoading;
  String? get error => _error;

  bool get isLoggedIn => _token != null; // 토큰 보유 여부로 로그인 상태 판단

  Future<void> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    final url = Uri.parse("http://192.168.50.221:8000/admin_auth/login"); // 실제 서버 주소/포트로 교체

    try {
      final resp = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: json.encode({"email": email, "password": password}),
      );

      if (resp.statusCode == 200) {
        final data = json.decode(resp.body);
        _token = data["access_token"];     // JWT 토큰
        _adminUser = data["admin_user"];   // {"id":..., "email":..., "name":..., ...}
      } else {
        _error = "로그인 실패(${resp.statusCode}): ${resp.body}";
      }
    } catch (e) {
      _error = "로그인 중 오류: $e";
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // --------------------------
  // 📌 로그아웃
  // --------------------------
  void logout() {
    _token = null;
    _adminUser = null;
    notifyListeners();
  }
}

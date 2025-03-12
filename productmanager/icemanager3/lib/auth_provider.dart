import 'package:flutter/material.dart';
import 'user.dart'; // 방금 만든 User 모델

class AuthProvider extends ChangeNotifier {
  User? _user; // 현재 로그인한 유저 정보 (없으면 null)

  User? get user => _user;

  bool get isLoggedIn => _user != null;

  // 로그인 성공 시 User 객체를 세팅
  void setUser(User newUser) {
    _user = newUser;
    notifyListeners(); // 값이 바뀌었음을 알림
  }

  // 로그아웃 시
  void clearUser() {
    _user = null;
    notifyListeners();
  }

  // ✅ 앱 실행 시 로그인 유지 확인
  void checkLoginStatus() {
    if (_user != null) {
      print("✅ 로그인 유지됨: ${_user!.name}");
    } else {
      print("⚠️ 로그인 세션 없음");
    }
  }
}

import 'package:flutter/material.dart';
import 'user.dart'; // 방금 만든 User 모델
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  User? _user; // 현재 로그인한 유저 정보 (없으면 null)
  final _storage = FlutterSecureStorage();
  User? get user => _user;

  bool get isLoggedIn => _user != null;

  // 로그인 성공 시 User 객체를 세팅
  Future<void> setUser(User newUser) async{
    _user = newUser;
    await _storage.write(key: 'access_token', value: newUser.token);
    notifyListeners(); // 값이 바뀌었음을 알림
  }

  // 로그아웃 시
  Future<void> clearUser() async{
    _user = null;
    await _storage.delete(key: 'access_token');
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

  // ✅ 앱 실행 시 자동 로그인 시도
  Future<void> tryAutoLogin() async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      // 서버에 요청하여 유저 정보 복원
      try {
        final userInfo = await ApiService.getMe(token);  // 🔹 사용자 정보 API 필요
        _user = User.fromJson({...userInfo, "token": token});
        print("✅ 자동 로그인 성공: ${_user!.name}");
        notifyListeners();
      } catch (e) {
        print("❌ 자동 로그인 실패: $e");
      }
    }
  }

}

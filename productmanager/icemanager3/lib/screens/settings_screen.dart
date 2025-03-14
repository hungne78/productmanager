import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../screens/login_screen.dart';  // ✅ 로그인 화면 import

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String _selectedMode = 'HID'; // 기본 모드

  @override
  void initState() {
    super.initState();
    _loadSelectedMode();
  }

  // 저장된 모드 불러오기
  Future<void> _loadSelectedMode() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _selectedMode = prefs.getString('scanner_mode') ?? 'HID';
    });
  }

  // 모드 변경 및 저장
  Future<void> _setSelectedMode(String mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('scanner_mode', mode);
    setState(() {
      _selectedMode = mode;
    });
  }

  // ✅ 로그아웃 기능 추가
  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();  // ✅ 모든 저장된 로그인 정보 삭제

    // ✅ 로그인 화면으로 이동
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("환경 설정")),
      body: Column(
        children: [
          ListTile(
            title: Text("바코드 스캐너 모드"),
          ),
          RadioListTile<String>(
            title: Text("HID 모드"),
            value: "HID",
            groupValue: _selectedMode,
            onChanged: (value) => _setSelectedMode(value!),
          ),
          RadioListTile<String>(
            title: Text("SPP 모드"),
            value: "SPP",
            groupValue: _selectedMode,
            onChanged: (value) => _setSelectedMode(value!),
          ),
          RadioListTile<String>(
            title: Text("BLE 모드"),
            value: "BLE",
            groupValue: _selectedMode,
            onChanged: (value) => _setSelectedMode(value!),
          ),
          const Divider(), // ✅ 구분선 추가
          ListTile(
            title: Text("로그아웃", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
            leading: Icon(Icons.exit_to_app, color: Colors.red),
            onTap: _logout,
          ),
        ],
      ),
    );
  }
}

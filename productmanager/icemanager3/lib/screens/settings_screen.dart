import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../screens/login_screen.dart';  // ✅ 로그인 화면 import
import '../screens/printer.dart';  // ✅ 프린터 다이얼로그 import

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String _selectedMode = 'HID'; // 기본 모드
  String _printerPaperSize = '80mm';
  String _printerLanguage = 'korean'; // korean / non-korean

  @override
  void initState() {
    super.initState();
    _loadSelectedMode();
  }

  // 저장된 모드 불러오기
  Future<void> _loadSelectedMode() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('scanner_mode');
    print("📦 불러온 스캐너 모드: $saved"); // ✅ 확인용 로그
    setState(() {
      _selectedMode = saved ?? 'HID'; // 저장된 값이 없으면 HID 사용
      _printerPaperSize = prefs.getString('printer_paper_size') ?? '80mm';
      _printerLanguage = prefs.getString('printer_language') ?? 'korean';
    });
  }

  // 모드 변경 및 저장
  Future<void> _setSelectedMode(String mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('scanner_mode', mode);
    print("✅ 저장된 스캐너 모드: $mode"); // ✅ 저장 확인 로그
    setState(() {
      _selectedMode = mode;
    });

    // ✅ 저장 후 사용자에게 알려주기
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("스캐너 모드 '$mode'로 저장되었습니다.")),
    );
  }
  Future<void> _setPrinterPaperSize(String size) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('printer_paper_size', size);
    setState(() {
      _printerPaperSize = size;
    });
  }

  Future<void> _setPrinterLanguage(String lang) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('printer_language', lang);
    setState(() {
      _printerLanguage = lang;
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
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        elevation: 2,
        leading: IconButton(
          icon: const Icon(Icons.home, color: Colors.white),
          onPressed: () => Navigator.pop(context), // 홈으로 돌아가기
        ),
        title: const Center(
          child: Text(
            "환경 설정",
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
          ),
        ),
        actions: [SizedBox(width: 48)], // 홈 버튼 공간 맞춤용
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          _buildSectionTitle("📦 바코드 스캐너 모드"),
          _buildRadioGroup(
            groupValue: _selectedMode,
            onChanged: _setSelectedMode,
            options: {
              "HID": "HID 모드",
              "SPP": "SPP 모드",
              "BLE": "BLE 모드",
            },
          ),

          const SizedBox(height: 16),
          _buildSectionTitle("🖨️ 프린터 용지 크기"),
          _buildRadioGroup(
            groupValue: _printerPaperSize,
            onChanged: _setPrinterPaperSize,
            options: {
              "55mm": "55mm 용지",
              "80mm": "80mm 용지",
            },
          ),

          const SizedBox(height: 16),
          _buildSectionTitle("🌐 프린터 언어"),
          _buildRadioGroup(
            groupValue: _printerLanguage,
            onChanged: _setPrinterLanguage,
            options: {
              "korean": "한글 지원 프린터",
              "non-korean": "한글 미지원 프린터",
            },
          ),

          const SizedBox(height: 24),
          Card(
            color: Colors.red.shade50,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: const Icon(Icons.exit_to_app, color: Colors.red),
              title: const Text(
                "로그아웃",
                style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red),
              ),
              onTap: _logout,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Text(
        title,
        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.indigo.shade700),
      ),
    );
  }

  Widget _buildRadioGroup({
    required String groupValue,
    required Function(String) onChanged,
    required Map<String, String> options,
  }) {
    return Column(
      children: options.entries.map((entry) {
        return Card(
          elevation: 1,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          child: RadioListTile<String>(
            title: Text(entry.value),
            value: entry.key,
            groupValue: groupValue,
            onChanged: (value) => onChanged(value!),
          ),
        );
      }).toList(),
    );
  }

}
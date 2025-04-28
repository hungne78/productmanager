// lib/features/calibration/view/calibration_screen.dart

import 'package:flutter/material.dart';
import 'package:live_trainer/widgets/live_camera_view.dart';

class CalibrationScreen extends StatefulWidget {
  const CalibrationScreen({super.key});

  @override
  State<CalibrationScreen> createState() => _CalibrationScreenState();
}

class _CalibrationScreenState extends State<CalibrationScreen> {
  final GlobalKey<LiveCameraViewState> _cameraKey = GlobalKey<LiveCameraViewState>();
  bool _cameraStarted = false;
  bool _measuring = false;
  String _result = "";
  double _userHeight = 0.0;
  final TextEditingController _heightController = TextEditingController();

  void _startMeasurement() {
    final input = _heightController.text;
    if (input.isEmpty || double.tryParse(input) == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("키(cm)를 정확히 입력해주세요.")),
      );
      return;
    }

    setState(() {
      _cameraStarted = true;   // 🔥 여기서 카메라 View를 등장시킴
      _measuring = true;
    });

    // 카메라 시작 후 0.5초정도 뒤에 startStream 해도 되고
    Future.delayed(const Duration(milliseconds: 500), () {
      _cameraKey.currentState?.startStream();
      _cameraKey.currentState?.startMeasurement();
    });
  }



  void _onMeasurementDone(Map<String, double> data) {
    setState(() {
      _measuring = false;
      _result = '''
어깨 너비: ${(data['shoulder']! * 100).toStringAsFixed(1)} cm
팔 길이: ${(data['arm']! * 100).toStringAsFixed(1)} cm
다리 길이: ${(data['leg']! * 100).toStringAsFixed(1)} cm
''';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('내 신체 사이즈 측정')),
      body: Stack(
        children: [
          if (_cameraStarted)  // 🔥 카메라 시작한 이후에만 보여준다!
            LiveCameraView(
              key: _cameraKey,
              mode: 'calibration',
              onMeasured: (data) {
                // 결과 처리
              },
            ),
          if (!_cameraStarted)  // 🔥 처음엔 이거만 보여
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  TextField(
                    controller: _heightController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: '당신의 키를 입력하세요 (cm)',
                      filled: true,
                      fillColor: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: _startMeasurement,
                    child: const Text("신체 사이즈 측정 시작"),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

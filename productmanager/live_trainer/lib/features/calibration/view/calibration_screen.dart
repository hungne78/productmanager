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
  bool _measuring = false;
  String _result = "";

  void _startMeasurement() {
    _cameraKey.currentState?.startMeasurement();
    setState(() {
      _measuring = true;
      _result = "측정 중... 3초만 기다려주세요!";
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
          LiveCameraView(
            key: _cameraKey,
            mode: 'calibration',
            onMeasured: _onMeasurementDone,
          ),
          if (!_measuring)
            Positioned(
              bottom: 30,
              left: 30,
              right: 30,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(200, 60),
                  textStyle: const TextStyle(fontSize: 20),
                ),
                onPressed: _startMeasurement,
                child: const Text("신체 사이즈 측정 시작"),
              ),
            ),
          if (_result.isNotEmpty)
            Positioned(
              top: 100,
              left: 30,
              right: 30,
              child: Text(
                _result,
                style: const TextStyle(fontSize: 22, color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
        ],
      ),
    );
  }
}

// lib/features/main_menu/main_menu_page.dart

import 'package:flutter/material.dart';
import 'package:live_trainer/features/calibration/view/calibration_screen.dart';
import 'package:live_trainer/features/recording/view/recording_screen.dart';
import 'package:live_trainer/features/training/view/training_screen.dart';

class MainMenuPage extends StatelessWidget {
  const MainMenuPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Live Trainer')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildButton(context, "1. 내 신체 사이즈 측정", const CalibrationScreen()),
            const SizedBox(height: 20),
            _buildButton(context, "2. 모범 자세 영상 촬영", const RecordingScreen()),
            const SizedBox(height: 20),
            _buildButton(context, "3. 실시간 운동 자세 피드백", const TrainingScreen()),
          ],
        ),
      ),
    );
  }

  Widget _buildButton(BuildContext context, String label, Widget screen) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(250, 60),
        textStyle: const TextStyle(fontSize: 18),
      ),
      onPressed: () {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => screen),
        );
      },
      child: Text(label),
    );
  }
}

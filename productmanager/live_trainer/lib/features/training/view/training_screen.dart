// lib/features/training/view/training_screen.dart

import 'package:flutter/material.dart';
import 'package:live_trainer/widgets/live_camera_view.dart';

class TrainingScreen extends StatelessWidget {
  const TrainingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('실시간 운동 피드백')),
      body: const LiveCameraView(mode: 'training'),
    );
  }
}

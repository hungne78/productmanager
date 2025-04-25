// lib/features/recording/view/recording_screen.dart

import 'package:flutter/material.dart';
import 'package:live_trainer/widgets/live_camera_view.dart';

class RecordingScreen extends StatelessWidget {
  const RecordingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('모범 자세 영상 촬영')),
      body: const LiveCameraView(mode: 'recording'),
    );
  }
}

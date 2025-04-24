// lib/features/calibration/view/calibration_page.dart

import 'dart:async';
import 'dart:ui' show Offset;
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:live_trainer/core/services/camera_service.dart';
import 'package:live_trainer/core/services/pose_estimator.dart';
import 'package:live_trainer/core/utils/angle_utils.dart';
import 'package:live_trainer/core/services/storage_service.dart';
import 'package:live_trainer/core/models/baseline.dart' as model;
import 'package:live_trainer/features/live_trainer/view/live_trainer_page.dart';

class CalibrationPage extends StatefulWidget {
  final StorageService storage;
  const CalibrationPage({Key? key, required this.storage}) : super(key: key);

  @override
  _CalibrationPageState createState() => _CalibrationPageState();
}

class _CalibrationPageState extends State<CalibrationPage> {
  final _cameraService = CameraService();
  final _poseEstimator = PoseEstimator();
  bool _ready = false;
  int _count = 3;
  final List<double> _shoulderAngles = [];
  final List<double> _hipAngles = [];

  @override
  void initState() {
    super.initState();
    _initAll();
  }

  Future<void> _initAll() async {
    await _cameraService.init();
    await _poseEstimator.init();
    setState(() => _ready = true);
    Timer.periodic(const Duration(seconds: 1), (t) {
      if (_count > 1) setState(() => _count--);
      else {
        t.cancel();
        _collectBaseline();
      }
    });
  }

  void _collectBaseline() {
    _cameraService.controller.startImageStream((img) {
      final lm = _poseEstimator.estimate(img);
      final sh = AngleUtils.angleBetweenPoints(
        a: Offset(lm[7].x, lm[7].y),
        b: Offset(lm[5].x, lm[5].y),
        c: Offset(lm[11].x, lm[11].y),
      );
      final hip = AngleUtils.angleBetweenPoints(
        a: Offset(lm[5].x, lm[5].y),
        b: Offset(lm[11].x, lm[11].y),
        c: Offset(lm[13].x, lm[13].y),
      );
      _shoulderAngles.add(sh);
      _hipAngles.add(hip);
    });

    Future.delayed(const Duration(seconds: 3), () async {
      await _cameraService.controller.stopImageStream();
      final baseSh = _shoulderAngles.reduce((a, b) => a + b) / _shoulderAngles.length;
      final baseHip = _hipAngles.reduce((a, b) => a + b) / _hipAngles.length;
      final bm = model.Baseline(baseSh, baseHip);
      await widget.storage.saveBaseline(bm);
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => LiveTrainerPage(
            baselineShoulder: baseSh,
            baselineHip: baseHip,
            storage: widget.storage,
          ),
        ),
      );
    });
  }

  @override
  void dispose() {
    _cameraService.dispose();
    _poseEstimator.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          CameraPreview(_cameraService.controller),
          Center(child: Text('$_count', style: const TextStyle(fontSize: 80, color: Colors.white))),
        ],
      ),
    );
  }
}

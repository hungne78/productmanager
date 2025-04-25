// lib/widgets/live_camera_view.dart

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:live_trainer/core/services/camera_service.dart';
import 'package:live_trainer/core/services/pose_estimator.dart';
import 'package:live_trainer/core/models/landmark.dart';
import 'package:live_trainer/features/live_trainer/view/skeleton_painter.dart';
import 'dart:async';
import 'dart:math';

class LiveCameraView extends StatefulWidget {
  final String mode;
  final Function(Map<String, double>)? onMeasured;

  const LiveCameraView({super.key, required this.mode, this.onMeasured});

  @override
  State<LiveCameraView> createState() => LiveCameraViewState();
}

class LiveCameraViewState extends State<LiveCameraView> {
  CameraController? _controller;
  List<CameraDescription>? _cameras;
  int _selectedCameraIdx = 0;

  final _poseEstimator = PoseEstimator();
  List<Landmark> _landmarks = [];
  bool _ready = false;

  bool _isMeasuring = false;
  final _shoulderDistances = <double>[];
  final _armLengths = <double>[];
  final _legLengths = <double>[];

  @override
  void initState() {
    super.initState();
    _setup();
  }

  Future<void> _setup() async {
    WidgetsFlutterBinding.ensureInitialized();
    _cameras = await availableCameras();
    await _initCamera(_selectedCameraIdx);
    await _poseEstimator.init();
  }

  Future<void> _initCamera(int idx) async {
    _controller?.dispose();
    _controller = CameraController(
      _cameras![idx],
      ResolutionPreset.medium,
      enableAudio: false,
    );
    await _controller!.initialize();
    _controller!.startImageStream((img) {
      final poses = _poseEstimator.estimate(img);

      if (_isMeasuring) {
        _collectMeasurement(poses);
      }

      setState(() => _landmarks = poses);
    });
    setState(() => _ready = true);
  }

  void switchCamera() async {
    if (_cameras == null || _cameras!.length < 2) return;
    setState(() => _ready = false);
    _selectedCameraIdx = (_selectedCameraIdx + 1) % _cameras!.length;
    await _initCamera(_selectedCameraIdx);
  }

  void startMeasurement() {
    _shoulderDistances.clear();
    _armLengths.clear();
    _legLengths.clear();
    _isMeasuring = true;

    Future.delayed(const Duration(seconds: 3), () {
      _isMeasuring = false;
      _finalizeMeasurement();
    });
  }

  void _collectMeasurement(List<Landmark> lm) {
    if (lm.length < 33) return;

    final shoulderDist = _distance(lm[11], lm[12]);
    final upperArm = _distance(lm[11], lm[13]);
    final lowerArm = _distance(lm[13], lm[15]);
    final armLength = upperArm + lowerArm;

    final upperLeg = _distance(lm[23], lm[25]);
    final lowerLeg = _distance(lm[25], lm[27]);
    final legLength = upperLeg + lowerLeg;

    _shoulderDistances.add(shoulderDist);
    _armLengths.add(armLength);
    _legLengths.add(legLength);
  }

  void _finalizeMeasurement() {
    double avgShoulder = _average(_shoulderDistances);
    double avgArm = _average(_armLengths);
    double avgLeg = _average(_legLengths);

    if (widget.onMeasured != null) {
      widget.onMeasured!({
        "shoulder": avgShoulder,
        "arm": avgArm,
        "leg": avgLeg,
      });
    }
  }

  double _distance(Landmark a, Landmark b) {
    return sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2));
  }

  double _average(List<double> list) {
    if (list.isEmpty) return 0.0;
    return list.reduce((a, b) => a + b) / list.length;
  }

  @override
  void dispose() {
    _controller?.dispose();
    _poseEstimator.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready || _controller == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return Stack(
      fit: StackFit.expand,
      children: [
        CameraPreview(_controller!),
        CustomPaint(
          painter: SkeletonPainter(_landmarks, _controller!.value.previewSize!),
        ),
        Positioned(
          top: 20,
          right: 20,
          child: IconButton(
            icon: const Icon(Icons.switch_camera, size: 40, color: Colors.white),
            onPressed: switchCamera,
          ),
        ),
      ],
    );
  }
}

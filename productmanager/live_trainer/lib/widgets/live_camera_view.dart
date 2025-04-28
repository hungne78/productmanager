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
  bool _cameraInitialized = false;
  bool _cameraInitializing = false;
  bool _poseReady = false;  // 🔥 추가: PoseEstimator 준비 여부

  late PoseEstimator _poseEstimator;

  List<Landmark> _landmarks = [];
  bool _ready = false;
  bool _streaming = false;

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
    try {
      _cameras = await availableCameras();
      await _initCamera(0);
      _poseEstimator = PoseEstimator();
      await _poseEstimator.init();
      _poseReady = true;
      print('✅ PoseEstimator initialized!');
      setState(() {
        _ready = true;
      });
    } catch (e) {
      print('❌ Setup failed: $e');
      _poseReady = false;
    }
  }


  Future<void> _initCamera(int idx) async {
    _controller?.dispose();
    _controller = CameraController(
      _cameras![idx],
      ResolutionPreset.medium,
      enableAudio: false,
    );
    await _controller!.initialize();
    _cameraInitialized = true;
    print('✅ CameraController 초기화 끝');
  }



  void startStream() {
    if (_controller == null || _streaming) return;
    if (!_cameraInitialized || !_poseReady) {
      print("Camera or Pose not ready yet, cannot start stream!");
      return;
    }

    _controller!.startImageStream((img) {
      if (!_poseReady) {
        print('PoseEstimator not ready, skipping frame.');
        return;
      }

      try {
        final poses = _poseEstimator.estimate(img);
        setState(() => _landmarks = poses);
      } catch (e) {
        print('PoseEstimator failed: $e');
      }
    });
    _streaming = true;
  }





  void switchCamera() async {
    if (_cameras == null || _cameras!.length < 2) return;
    setState(() => _ready = false);

    try {
      if (_controller != null && _controller!.value.isStreamingImages) {
        await _controller!.stopImageStream();
      }
      await _controller?.dispose();
      _poseEstimator.dispose();
    } catch (e) {
      print('Error stopping camera or pose estimator: $e');
    }

    _selectedCameraIdx = (_selectedCameraIdx + 1) % _cameras!.length;

    // 👉 1. 포즈 추정기 먼저 새로 만들어
    final newPoseEstimator = PoseEstimator();
    await newPoseEstimator.init();

    // 👉 2. 새 PoseEstimator가 준비된 후
    _poseEstimator = newPoseEstimator;

    // 👉 3. 그 다음에 카메라를 연다
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

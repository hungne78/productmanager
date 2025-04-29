import 'dart:async';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:live_trainer/core/services/camera_service.dart';
import 'package:live_trainer/core/services/pose_estimator.dart';
import 'package:live_trainer/core/services/pose_analyzer.dart';
import 'package:live_trainer/core/services/tts_manager.dart';
import 'package:live_trainer/core/models/landmark.dart';
import 'package:live_trainer/features/live_trainer/view/skeleton_painter.dart';
import 'package:live_trainer/core/services/storage_service.dart';

class LiveTrainerPage extends StatefulWidget {
  final double baselineShoulder;
  final double baselineHip;
  final StorageService storage;

  const LiveTrainerPage({
    Key? key,
    required this.baselineShoulder,
    required this.baselineHip,
    required this.storage,
  }) : super(key: key);

  @override
  _LiveTrainerPageState createState() => _LiveTrainerPageState();
}

class _LiveTrainerPageState extends State<LiveTrainerPage> {
  final _cameraService = CameraService();
  final _poseEstimator = PoseEstimator();
  late final PoseAnalyzer _analyzer;
  late final TtsManager _ttsMgr;

  List<Landmark> _landmarks = [];
  bool _ready = false;
  bool _poseReady = false;
  bool _measuring = false;
  int _countdown = 0;

  @override
  void initState() {
    super.initState();
    _analyzer = PoseAnalyzer(
      baselineShoulder: widget.baselineShoulder,
      baselineHip: widget.baselineHip,
    );
    _ttsMgr = TtsManager();
    _setup();
  }

  Future<void> _setup() async {
    await _cameraService.init();
    await _poseEstimator.init();
    setState(() {
      _ready = true;
      _poseReady = true;
    });
  }

  void _startMeasurement() {
    setState(() {
      _countdown = 3;
      _measuring = false;
    });

    Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() => _countdown--);
      if (_countdown == 0) {
        timer.cancel();
        _beginPoseStream();
      }
    });
  }

  void _beginPoseStream() {
    if (!_poseReady) {
      debugPrint("⚠️ PoseEstimator not ready. Stream not started.");
      return;
    }

    _cameraService.startStream((img) {
      final poses = _poseEstimator.estimate(img);
      if (poses.isEmpty) return;

      final msgs = _analyzer.analyze(poses);
      _ttsMgr.enqueue(msgs);

      setState(() {
        _landmarks = poses;
        _measuring = true;
      });
    });
  }

  @override
  void dispose() {
    _cameraService.dispose();
    _poseEstimator.dispose();
    _ttsMgr.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Live Trainer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.flip_camera_android),
            onPressed: () async {
              await _cameraService.switchCamera();
              _beginPoseStream(); // 전환 후 재시작
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Stack(
          fit: StackFit.expand,
          children: [
            CameraPreview(_cameraService.controller),
            CustomPaint(
              painter: SkeletonPainter(
                _landmarks,
                _cameraService.controller.value.previewSize!,
              ),
            ),
            if (_countdown > 0)
              Center(
                child: Text(
                  '$_countdown',
                  style: const TextStyle(fontSize: 80, color: Colors.white),
                ),
              ),
            if (!_measuring && _countdown == 0 && _poseReady)
              Align(
                alignment: Alignment.bottomCenter,
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: ElevatedButton(
                    onPressed: _startMeasurement,
                    child: const Text('측정 시작'),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// lib/features/live_trainer/view/live_trainer_page.dart
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:live_trainer/core/services/camera_service.dart';
import 'package:live_trainer/core/services/pose_estimator.dart';
import 'package:live_trainer/core/services/pose_analyzer.dart';
import 'package:live_trainer/core/services/tts_manager.dart';
import 'package:live_trainer/core/models/landmark.dart';
import 'package:live_trainer/features/live_trainer/view/skeleton_painter.dart';

// **여기** StorageService import 추가
import 'package:live_trainer/core/services/storage_service.dart';
import 'package:live_trainer/features/settings/view/settings_page.dart';

class LiveTrainerPage extends StatefulWidget {
  final double baselineShoulder;
  final double baselineHip;
  final StorageService storage;  // ← 추가

  const LiveTrainerPage({
    Key? key,
    required this.baselineShoulder,
    required this.baselineHip,
    required this.storage,        // ← 추가
  }) : super(key: key);

  @override
  _LiveTrainerPageState createState() => _LiveTrainerPageState();
}

class _LiveTrainerPageState extends State<LiveTrainerPage> {
  final _cameraService = CameraService();
  final _poseEstimator = PoseEstimator();
  late final PoseAnalyzer _analyzer;
  final _ttsMgr = TtsManager();

  List<Landmark> _landmarks = [];
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _analyzer = PoseAnalyzer(
      baselineShoulder: widget.baselineShoulder,
      baselineHip: widget.baselineHip,
    );
    _setup();
  }

  Future<void> _setup() async {
    await _cameraService.init();
    await _poseEstimator.init();

    _cameraService.controller.startImageStream((img) {
      final poses = _poseEstimator.estimate(img);
      final msgs = _analyzer.analyze(poses);
      _ttsMgr.enqueue(msgs);
      setState(() => _landmarks = poses);
    });

    setState(() => _ready = true);
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
      // **이 부분** appBar 추가
      appBar: AppBar(
        title: const Text('Live Trainer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => SettingsPage(storage: widget.storage),
                ),
              );
            },
          ),
        ],
      ),
      body: Stack(
        fit: StackFit.expand,
        children: [
          CameraPreview(_cameraService.controller),
          CustomPaint(
            painter: SkeletonPainter(
              _landmarks,
              _cameraService.controller.value.previewSize!,
            ),
          ),
        ],
      ),
    );
  }
}

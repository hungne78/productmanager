import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:live_trainer/core/services/camera_service.dart';
import 'package:live_trainer/core/services/pose_estimator.dart';
import 'package:live_trainer/features/live_trainer/view/skeleton_painter.dart';
import 'package:live_trainer/core/models/landmark.dart';
import 'package:live_trainer/core/services/pose_analyzer.dart';
import 'package:live_trainer/core/services/tts_manager.dart';

class LiveTrainerPage extends StatefulWidget {
  const LiveTrainerPage({Key? key}) : super(key: key);
  @override
  _LiveTrainerPageState createState() => _LiveTrainerPageState();
}

class _LiveTrainerPageState extends State<LiveTrainerPage> {
  final _cameraService = CameraService();
  final _poseEstimator = PoseEstimator();

  List<Landmark> _landmarks = [];
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _setup();
  }

  Future<void> _setup() async {
    await _cameraService.init();
    await _poseEstimator.init();
    final _analyzer = PoseAnalyzer();
    final _ttsMgr = TtsManager();
    // 프레임 스트림 리스너
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
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          CameraPreview(_cameraService.controller),
          CustomPaint(
            painter: SkeletonPainter(_landmarks, _cameraService.controller.value.previewSize!),
          ),
        ],
      ),
    );
  }
}

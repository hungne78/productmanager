// lib/core/services/camera_service.dart

import 'package:camera/camera.dart';

class CameraService {
  final List<CameraDescription> _cameras = [];
  CameraController? _controller;
  int _current = 0;             // 0 = 후면, 1 = 전면 (일반적인 순서)

  Future<void> init() async {
    _cameras.addAll(await availableCameras());
    await _open(_current);      // 기본은 0번
  }

  CameraController get controller => _controller!;

  Future<void> switchCamera() async {
    // ① 스트림이 돌고 있으면 중단
    if (_controller?.value.isStreamingImages == true) {
      await _controller!.stopImageStream();
    }
    // ② dispose
    await _controller?.dispose();

    // ③ 다음 카메라 index 계산
    _current = (_current + 1) % _cameras.length;

    // ④ 새 컨트롤러 생성
    await _open(_current);
  }

  Future<void> _open(int index) async {
    _controller = CameraController(
      _cameras[index],
      ResolutionPreset.medium,
      enableAudio: false,
    );
    await _controller!.initialize();
  }

  Future<void> startStream(
      void Function(CameraImage img) onFrame) async {
    if (!_controller!.value.isInitialized) {
      throw Exception('카메라 초기화 안 됨');
    }
    await _controller!.startImageStream(onFrame);
  }

  void dispose() => _controller?.dispose();



}

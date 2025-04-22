// lib/core/services/camera_service.dart

import 'package:camera/camera.dart';

class CameraService {
  CameraController? _controller;

  /// 초기화: 사용 가능한 첫 번째 카메라를 ResolutionPreset.medium 으로 세팅
  Future<void> init() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) {
      throw CameraException('NoCamera', '디바이스에 카메라가 없습니다.');
    }
    _controller = CameraController(
      cameras.first,
      ResolutionPreset.medium,
      enableAudio: false,
    );
    await _controller!.initialize();
  }

  CameraController get controller {
    if (_controller == null || !_controller!.value.isInitialized) {
      throw CameraException('Uninitialized', 'CameraService가 init되지 않았습니다.');
    }
    return _controller!;
  }

  void dispose() {
    _controller?.dispose();
  }
}

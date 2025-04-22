// lib/core/services/pose_estimator.dart

import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:camera/camera.dart';
import 'package:image/image.dart' as imglib;
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:live_trainer/core/models/landmark.dart';

class PoseEstimator {
  late Interpreter _interpreter;
  final int _inputSize = 192;

  PoseEstimator();

  Future<void> init() async {
    _interpreter = await Interpreter.fromAsset(
      'assets/models/movenet_lightning.tflite',
      options: InterpreterOptions()..addDelegate(GpuDelegateV2()),
    );
  }

  List<Landmark> estimate(CameraImage img) {
    // 1) YUV → imglib.Image
    final imglib.Image rgb = _yuvToRgb(img);

    // 2) 리사이즈
    final imglib.Image resized = imglib.copyResize(rgb, width: _inputSize, height: _inputSize);

    // 3) Float32List 버퍼 만들기 (정규화 포함)
    final input = _imageToFloat32List(resized);

    // 4) 모델 실행
    final List<List<List<double>>> output = List.generate(
      1,
          (_) => List.generate(17, (_) => List<double>.filled(3, 0.0)),
    );
    _interpreter.run(input, output);

    // 5) 결과 파싱
    return _parseOutput(output);
  }

  imglib.Image _yuvToRgb(CameraImage img) {
    final w = img.width, h = img.height;
    final imglib.Image image = imglib.Image(w, h);
    final pY = img.planes[0], pU = img.planes[1], pV = img.planes[2];
    for (int y = 0; y < h; y++) {
      for (int x = 0; x < w; x++) {
        final yp = pY.bytes[y * pY.bytesPerRow + x];
        final uvIndex = (y >> 1) * pU.bytesPerRow + (x >> 1) * pU.bytesPerPixel!;
        final up = pU.bytes[uvIndex], vp = pV.bytes[uvIndex];
        final r = (yp + 1.370705 * (vp - 128)).round().clamp(0, 255);
        final g = (yp - 0.337633 * (up - 128) - 0.698001 * (vp - 128)).round().clamp(0, 255);
        final b = (yp + 1.732446 * (up - 128)).round().clamp(0, 255);
        image.setPixelRgba(x, y, r, g, b);
      }
    }
    return image;
  }

  Float32List _imageToFloat32List(imglib.Image img) {
    final bytes = Float32List(_inputSize * _inputSize * 3);
    int idx = 0;
    for (var y = 0; y < _inputSize; y++) {
      for (var x = 0; x < _inputSize; x++) {
        final px = img.getPixel(x, y);
        bytes[idx++] = ((imglib.getRed(px)) / 255.0);
        bytes[idx++] = ((imglib.getGreen(px)) / 255.0);
        bytes[idx++] = ((imglib.getBlue(px)) / 255.0);
      }
    }
    return bytes;
  }

  List<Landmark> _parseOutput(List<List<List<double>>> output) {
    final List<Landmark> lm = [];
    for (var i = 0; i < 17; i++) {
      final x = output[0][i][1];
      final y = output[0][i][0];
      final score = output[0][i][2];
      lm.add(Landmark(x, y, score));
    }
    return lm;
  }

  void dispose() => _interpreter.close();
}

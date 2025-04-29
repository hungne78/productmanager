// lib/core/services/pose_estimator.dart

import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:camera/camera.dart';
import 'package:image/image.dart' as imglib;
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:live_trainer/core/models/landmark.dart';

class PoseEstimator {
  late Interpreter _interpreter;
  int _inputSize = 192;

  PoseEstimator();

  Future<void> init() async {
    _interpreter = await Interpreter.fromAsset(
      'assets/models/pose_landmark_full.tflite',
      options: InterpreterOptions()..addDelegate(GpuDelegateV2()),
    );

    final inputShape = _interpreter.getInputTensor(0).shape;
    _inputSize = inputShape[1];  // (보통 256 또는 224 또는 192)

    print('✅ 모델 inputSize: $_inputSize');

    // ❗ 여기서 resizeInputTensor(), allocateTensors() 절대 호출하지 마라
  }




  List<Landmark> estimate(CameraImage img) {
    final rgb = _yuvToRgb(img);
    final resized = imglib.copyResize(rgb, width: _inputSize, height: _inputSize);
    final input = _imageToFloat32List(resized);

    final List<List<double>> output = List.generate(
      1,
          (_) => List.filled(195, 0.0),
    );

    _interpreter.run(input, output);

    final landmarks = _parseOutput(output);

    // 최소 신뢰도 0.3 이상인 포인트가 5개 이상 없으면 skip
    final validCount = landmarks.where((lm) => lm.score > 0.3).length;
    if (validCount < 5) {
      print("⚠️ 사람 없음 또는 landmark 신뢰도 낮음 → 분석 skip");
      return [];
    }

    return landmarks;
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

  Uint8List _imageToFloat32List(imglib.Image image) {
    final Float32List input = Float32List(1 * _inputSize * _inputSize * 3);
    final buffer = input.buffer.asFloat32List();

    int pixelIndex = 0;
    for (int y = 0; y < _inputSize; y++) {
      for (int x = 0; x < _inputSize; x++) {
        final pixel = image.getPixel(x, y);
        buffer[pixelIndex++] = (imglib.getRed(pixel) / 255.0);
        buffer[pixelIndex++] = (imglib.getGreen(pixel) / 255.0);
        buffer[pixelIndex++] = (imglib.getBlue(pixel) / 255.0);
      }
    }
    return input.buffer.asUint8List();
  }

  List<Landmark> _parseOutput(List<List<double>> output) {
    final List<Landmark> landmarks = [];
    final flat = output[0]; // 길이 195 (39 x 5)

    for (int i = 0; i < 39; i++) {
      final x = flat[i * 5];
      final y = flat[i * 5 + 1];
      final z = flat[i * 5 + 2];
      final visibility = flat[i * 5 + 3];
      final presence = flat[i * 5 + 4];
      landmarks.add(Landmark(x, y, z, visibility, presence)); // ✅ 5개 전달
    }

    return landmarks;
  }







  void dispose() => _interpreter.close();
}

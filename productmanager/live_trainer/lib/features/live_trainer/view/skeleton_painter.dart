import 'package:flutter/material.dart';
import 'package:live_trainer/core/services/pose_estimator.dart';
import 'package:live_trainer/core/models/landmark.dart';

class SkeletonPainter extends CustomPainter {
  final List<Landmark> landmarks;
  final Size previewSize;
  SkeletonPainter(this.landmarks, this.previewSize);


  static const _pairs = [
    [0,1],[1,2],[2,3],[3,7],
    [0,4],[4,5],[5,6],[6,8],
    [9,10],
    [11,12],
    [11,13],[13,15],
    [12,14],[14,16],
    [11,23],[12,24],
    [23,24],
    [23,25],[24,26],
    [25,27],[26,28],
    [27,29],[28,30],
    [29,31],[30,32]
  ];


  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke
      ..color = Colors.greenAccent;

    Offset _transform(Landmark lm) {
      return Offset(lm.x * size.width, lm.y * size.height);
    }

    for (var p in _pairs) {
      final a = landmarks[p[0]];
      final b = landmarks[p[1]];
      if (a.visibility > 0.3 && b.visibility > 0.3) {  // 🔥 visibility로 변경
        canvas.drawLine(_transform(a), _transform(b), paint);
      }
    }

    for (var lm in landmarks) {
      if (lm.visibility > 0.3) {  // 🔥 visibility로 변경
        canvas.drawCircle(_transform(lm), 4, paint..style = PaintingStyle.fill);
      }
    }
  }

  @override
  bool shouldRepaint(covariant SkeletonPainter old) =>
      old.landmarks != landmarks;

}

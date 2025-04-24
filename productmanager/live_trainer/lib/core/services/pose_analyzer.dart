// lib/core/services/pose_analyzer.dart

import 'package:live_trainer/core/models/landmark.dart';
import 'package:live_trainer/core/utils/angle_utils.dart';
import 'dart:ui' show Offset;

class PoseAnalyzer {
  final double baselineShoulder;
  final double baselineHip;
  PoseAnalyzer({
    required this.baselineShoulder,
    required this.baselineHip,
  });

  bool isShoulderRaised(List<Landmark> lm) {
    final angle = AngleUtils.angleBetweenPoints(
      a: Offset(lm[7].x, lm[7].y),
      b: Offset(lm[5].x, lm[5].y),
      c: Offset(lm[11].x, lm[11].y),
    );
    return angle < baselineShoulder - 5; // 기준보다 5° 이상 높으면
  }

  bool isBackBent(List<Landmark> lm) {
    final angle = AngleUtils.angleBetweenPoints(
      a: Offset(lm[5].x, lm[5].y),
      b: Offset(lm[11].x, lm[11].y),
      c: Offset(lm[13].x, lm[13].y),
    );
    return angle < baselineHip - 5; // 기준보다 5° 이상 작으면
  }

  bool isKneeStraight(List<Landmark> lm) {
    // 왼쪽 무릎 기준 (11-13-15)
    final angle = AngleUtils.angleBetweenPoints(
      a: Offset(lm[11].x, lm[11].y),
      b: Offset(lm[13].x, lm[13].y),
      c: Offset(lm[15].x, lm[15].y),
    );
    return angle > 170; // 거의 펴져 있으면
  }

  List<String> analyze(List<Landmark> lm) {
    final msgs = <String>[];
    if (isShoulderRaised(lm)) msgs.add('어깨를 살짝 내려 주세요');
    if (isBackBent(lm)) msgs.add('허리를 곧게 펴 주세요');
    if (isKneeStraight(lm)) msgs.add('무릎을 조금 더 구부려 주세요');
    return msgs;
  }
}

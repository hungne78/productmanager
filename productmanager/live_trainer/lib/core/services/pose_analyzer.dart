import 'package:live_trainer/core/models/landmark.dart';
import 'package:live_trainer/core/utils/angle_utils.dart';
import 'dart:ui' show Offset;
class PoseAnalyzer {
  /// 어깨가 5° 이상 올라갔는지
  bool isShoulderRaised(List<Landmark> lm) {
    final leftShoulder = lm[5], leftElbow = lm[7], leftHip = lm[11];
    final angle = AngleUtils.angleBetweenPoints(
      a: Offset(leftElbow.x, leftElbow.y),
      b: Offset(leftShoulder.x, leftShoulder.y),
      c: Offset(leftHip.x, leftHip.y),
    );
    return angle < 85; // 90° 기준 5° 차이
  }

  /// 분석 결과 메시지 리스트
  List<String> analyze(List<Landmark> lm) {
    final msgs = <String>[];
    if (isShoulderRaised(lm)) msgs.add('어깨를 살짝 내려 주세요');
    // TODO: 허리·무릎 등 추가
    return msgs;
  }
}

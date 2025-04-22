import 'dart:math';
import 'dart:ui' show Offset;
class AngleUtils {
  /// 세 점(a–b–c)에서 ∠abc (degree) 계산
  static double angleBetweenPoints({
    required Offset a,
    required Offset b,
    required Offset c,
  }) {
    final v1 = Offset(a.dx - b.dx, a.dy - b.dy);
    final v2 = Offset(c.dx - b.dx, c.dy - b.dy);
    final dot = v1.dx * v2.dx + v1.dy * v2.dy;
    final mag1 = sqrt(v1.dx * v1.dx + v1.dy * v1.dy);
    final mag2 = sqrt(v2.dx * v2.dx + v2.dy * v2.dy);
    return acos(dot / (mag1 * mag2)) * (180 / pi);
  }
}

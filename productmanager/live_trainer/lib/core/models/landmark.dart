// lib/core/models/landmark.dart

class Landmark {
  final double x;
  final double y;
  final double z;
  final double visibility;
  final double presence;

  Landmark(
      this.x,
      this.y,
      this.z,
      this.visibility,
      this.presence,
      );

  /// 기존 MoveNet 호환을 위한 가짜 score (MediaPipe에선 presence 사용)
  double get score => presence;
}

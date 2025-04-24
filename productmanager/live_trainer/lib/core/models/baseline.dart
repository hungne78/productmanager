// lib/core/models/baseline.dart
import 'package:hive/hive.dart';

part 'baseline.g.dart';

@HiveType(typeId: 0)
class Baseline {
  @HiveField(0)
  final double shoulder;
  @HiveField(1)
  final double hip;

  Baseline(this.shoulder, this.hip);
}

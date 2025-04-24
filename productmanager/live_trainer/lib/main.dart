// lib/main.dart

import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:live_trainer/core/services/storage_service.dart';
// 모델 Baseline 을 충돌 없이 불러오기 위해 alias 사용
import 'package:live_trainer/core/models/baseline.dart' as model;

import 'package:live_trainer/features/calibration/view/calibration_page.dart';
import 'package:live_trainer/features/live_trainer/view/live_trainer_page.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();

  final storage = StorageService();
  await storage.init();

  // model.Baseline? 타입
  final model.Baseline? baseline = storage.loadBaseline();

  runApp(MyApp(baseline: baseline, storage: storage));
}

class MyApp extends StatelessWidget {
  final model.Baseline? baseline;
  final StorageService storage;
  const MyApp({
    super.key,
    required this.baseline,
    required this.storage,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Live Trainer',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: baseline == null
      // 저장된 캘리값이 없으면 캘리 페이지
          ? CalibrationPage(storage: storage)
      // 있으면 non-null 단언자 (!) 로 꺼내서
          : LiveTrainerPage(
        baselineShoulder: baseline!.shoulder,  // ← baseline!
        baselineHip: baseline!.hip,            // ← baseline!
        storage: storage,                      // storage 넘기기
      ),
    );
  }
}

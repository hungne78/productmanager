// lib/main.dart

import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:live_trainer/core/services/storage_service.dart';
import 'package:live_trainer/features/main_menu/main_menu_page.dart'; // ⭐ MainMenuPage import

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();

  final storage = StorageService();
  await storage.init();

  runApp(MyApp(storage: storage));
}

class MyApp extends StatelessWidget {
  final StorageService storage;
  const MyApp({super.key, required this.storage});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Live Trainer',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const MainMenuPage(), // ⭐ 여기! 무조건 3버튼 화면 띄우기
    );
  }
}

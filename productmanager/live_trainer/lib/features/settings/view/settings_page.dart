// lib/features/settings/view/settings_page.dart
import 'package:flutter/material.dart';
import 'package:live_trainer/core/services/storage_service.dart';
import 'package:live_trainer/features/calibration/view/calibration_page.dart';

class SettingsPage extends StatelessWidget {
  final StorageService storage;
  const SettingsPage({super.key, required this.storage});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('설정')),
      body: Center(
        child: ElevatedButton(
          child: const Text('캘리 다시하기'),
          onPressed: () {
            storage.clearBaseline();
            Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(
                builder: (_) => CalibrationPage(storage: storage),
              ),
                  (_) => false,
            );
          },
        ),
      ),
    );
  }
}

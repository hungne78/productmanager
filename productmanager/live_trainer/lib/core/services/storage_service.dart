// lib/core/services/storage_service.dart
import 'package:hive/hive.dart';
import 'package:live_trainer/core/models/baseline.dart';

class StorageService {
  static const _boxName = 'settings';

  Future<void> init() async {
    Hive.registerAdapter(BaselineAdapter());
    await Hive.openBox<Baseline>(_boxName);
  }

  Baseline? loadBaseline() {
    final box = Hive.box<Baseline>(_boxName);
    return box.get('baseline');
  }

  Future<void> saveBaseline(Baseline b) async {
    final box = Hive.box<Baseline>(_boxName);
    await box.put('baseline', b);
  }

  Future<void> clearBaseline() async {
    final box = Hive.box<Baseline>(_boxName);
    await box.delete('baseline');
  }
}

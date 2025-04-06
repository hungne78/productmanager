import 'package:soundpool/soundpool.dart';
import 'package:flutter/services.dart';

class SoundManager {
  final Soundpool _soundpool = Soundpool.fromOptions();
  int? _validBeepId;
  int? _invalidBeepId;

  Future<void> loadSounds() async {
    _validBeepId = await _soundpool.load(await rootBundle.load("assets/sounds/valid_beep.wav"));
    _invalidBeepId = await _soundpool.load(await rootBundle.load("assets/sounds/invalid_beep.wav"));
  }

  void playValidBeep() {
    if (_validBeepId != null) {
      _soundpool.play(_validBeepId!);
    }
  }

  void playInvalidBeep() {
    if (_invalidBeepId != null) {
      _soundpool.play(_invalidBeepId!);
    }
  }
}

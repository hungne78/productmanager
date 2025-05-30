import 'package:audioplayers/audioplayers.dart';

class SoundManager {
  final AudioPlayer _player = AudioPlayer();

  Future<void> playValid() async {
    await _player.play(AssetSource('sounds/valid_beep.wav'));
  }

  Future<void> playInvalid() async {
    await _player.play(AssetSource('sounds/invalid_beep.wav'));
  }
}

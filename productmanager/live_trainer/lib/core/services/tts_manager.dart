import 'dart:async';
import 'package:flutter_tts/flutter_tts.dart';

class TtsManager {
  final _tts = FlutterTts();
  final _queue = <String>[];
  bool _speaking = false;

  TtsManager() {
    _tts.setLanguage('ko-KR');
    _tts.setSpeechRate(0.5);
  }

  void enqueue(List<String> msgs) {
    _queue.addAll(msgs);
    _processQueue();
  }

  Future<void> _processQueue() async {
    if (_speaking || _queue.isEmpty) return;
    _speaking = true;
    final msg = _queue.removeAt(0);
    await _tts.speak(msg);
    await Future.delayed(const Duration(seconds: 2));
    _speaking = false;
    _processQueue();
  }

  void dispose() => _tts.stop();
}

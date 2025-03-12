package com.example.icemanager3

import android.content.Intent
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.embedding.engine.FlutterEngineCache

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        println("✅ MainActivity onCreate 호출됨")
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        FlutterEngineCache.getInstance().put("my_engine_id", flutterEngine)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        println("✅ MainActivity: onNewIntent 호출됨 (기존 액티비티 유지)")
    }

    override fun onDestroy() {
        println("⚠️ MainActivity: onDestroy 호출됨 → 방지")
        moveTaskToBack(true) // ✅ 앱이 종료되지 않고 백그라운드로 이동하도록 변경
        super.onDestroy()
    }
}

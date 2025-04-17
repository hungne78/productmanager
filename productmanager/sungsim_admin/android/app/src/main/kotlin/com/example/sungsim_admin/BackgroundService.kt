package com.example.sungsim_admin

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log

class BackgroundService : Service() {

    override fun onCreate() {
        super.onCreate()
        Log.d("BackgroundService", "✅ 백그라운드 서비스 시작됨")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d("BackgroundService", "✅ 서비스 실행 중...")
        return START_STICKY  // ✅ 서비스가 종료되지 않고 계속 실행되도록 설정
    }

    override fun onDestroy() {
        Log.d("BackgroundService", "⚠️ 백그라운드 서비스 종료됨 → 다시 시작")
        super.onDestroy()
        val restartService = Intent(this, BackgroundService::class.java)
        startService(restartService)
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
}

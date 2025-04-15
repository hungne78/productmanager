import 'package:flutter/material.dart';
import 'dart:async';
import 'package:firebase_core/firebase_core.dart'; // 🔹 추가
import 'package:firebase_messaging/firebase_messaging.dart'; // 🔹 추가

import 'screens/login_screen.dart';
import 'package:provider/provider.dart';
import 'auth_provider.dart';
import 'product_provider.dart';
import 'vehicle_stock_provider.dart';
import 'screens/home_screen.dart';
import 'screens/settings_screen.dart';
import 'bluetooth_printer_provider.dart';
import 'firebase_options.dart';


Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp(); // 🔹 백그라운드 알림 수신 시 필수
  print("🔔 [백그라운드] 메시지 수신: ${message.notification?.title}");
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized(); // 🔹 Firebase 초기화 전에 필요
  // await Firebase.initializeApp(); // 🔹 Firebase 연결
  final authProvider = AuthProvider();
  await authProvider.tryAutoLogin(); // ✅ 자동 로그인 시도
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler); // 🔹 백그라운드 처리

  runZonedGuarded(() {
    runApp(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>.value(value: authProvider),
          ChangeNotifierProvider<ProductProvider>(create: (_) => ProductProvider()),
          ChangeNotifierProvider<VehicleStockProvider>(create: (_) => VehicleStockProvider()),
          ChangeNotifierProvider(create: (context) => BluetoothPrinterProvider()),
        ],
        child: const MyApp(),
      ),
    );
  }, (error, stackTrace) {
    debugPrint("❌ Flutter 앱 크래시 발생: $error");
    debugPrint("📌 StackTrace: $stackTrace");
  });
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'My Flutter App',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: authProvider.user == null
          ? const LoginScreen()
          : HomeScreen(token: authProvider.user!.token),
    );
  }
}

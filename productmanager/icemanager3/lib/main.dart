import 'package:flutter/material.dart';
import 'dart:async';
import 'screens/login_screen.dart';  // 우리가 만든 로그인 화면 import
import 'package:provider/provider.dart';
import 'auth_provider.dart'; // 인증 관련 Provider
import 'product_provider.dart'; // 상품 관련 Provider
import 'vehicle_stock_provider.dart'; // 차량 재고 관련 Provider
import 'screens/home_screen.dart';
import 'screens/settings_screen.dart';
import 'bluetooth_printer_provider.dart';
void main() {
  runZonedGuarded(() {
    runApp(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<AuthProvider>(
            create: (_) => AuthProvider(),
          ),
          ChangeNotifierProvider<ProductProvider>(
            create: (_) => ProductProvider(),
          ),
          ChangeNotifierProvider<VehicleStockProvider>(
            create: (_) => VehicleStockProvider(),
          ),
          ChangeNotifierProvider(create: (context) => BluetoothPrinterProvider()),
        ],

        child: const MyApp(), // ✅ `MaterialApp`을 여기서 호출해야 함!
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

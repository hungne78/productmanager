import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/franchise_login_screen.dart';
import 'screens/franchise_order_screen.dart';
import 'screens/franchise_date_select_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/product_provider.dart';
import 'package:intl/date_symbol_data_local.dart'; // ✅ 필수
import 'package:franchise_order/main.dart'; // ← 앱 엔트리 파일

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ✅ 한국어 로케일 데이터 초기화
  await initializeDateFormatting('ko_KR', null);
  runApp(const FranchiseApp());
}

class FranchiseApp extends StatelessWidget {
  const FranchiseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ProductProvider()),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        title: '점주 주문 앱',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          fontFamily: 'Pretendard',
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => const FranchiseLoginScreen(),
          '/select_date': (context) => const FranchiseDateSelectScreen(),
          // '/order': 제거!
        },
      ),
    );
  }
}

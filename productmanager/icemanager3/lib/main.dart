import 'package:flutter/material.dart';
import 'screens/login_screen.dart';  // 우리가 만든 파일 import
import 'package:provider/provider.dart';
import 'auth_provider.dart'; // 방금 만든 ChangeNotifier
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthProvider>(
          create: (_) => AuthProvider(),
        ),
        // ↑ 필요하다면 다른 Provider도 등록
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'My Flutter App',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const LoginScreen(),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'client_screen.dart';
import 'product_screen.dart';
import 'sales_screen.dart';
import './/auth_provider.dart';  // AuthProvider 임포트
// ... 기타 기능 화면 import

class HomeScreen extends StatelessWidget {
  final String token;
  const HomeScreen({Key? key, required this.token}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Provider에서 AuthProvider 꺼내기
    final auth = context.watch<AuthProvider>();
    final user = auth.user; // null이거나 User 객체(로그인 성공 시 setUser()됨)

    // 9개 아이콘 정보를 담을 리스트(예시)
    // 여기서 하나를 "판매"로 예시
    final List<_MenuItem> menuItems = [
      // -------------------------------
      // ① "판매" 메뉴 아이템(예시)
      // -------------------------------
      _MenuItem("판매", "assets/images/icon_sales.png", () {
        if (user == null) {
          // 아직 로그인이 안 된 경우 처리
          // 예: 에러 메시지 띄우거나, 로그인 화면으로 이동
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("로그인 정보가 없습니다.")),
          );
        } else {
          // user.token, user.id 등을 SalesScreen에 넘겨주거나,
          // 혹은 SalesScreen에서 Provider를 다시 사용해도 됩니다.
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => SalesScreen(
                token: user.token,
                employeeId: user.id,
              ),
            ),
          );
        }
      }),

      // -------------------------------
      // ② 거래처
      // -------------------------------
      _MenuItem("거래처", "assets/images/icon_client.png", () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ClientScreen(token: token)),
        );
      }),

      // -------------------------------
      // ③ 상품
      // -------------------------------
      _MenuItem("상품", "assets/images/icon_product.png", () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ProductScreen(token: token)),
        );
      }),

      // ... 나머지 6~7개
      _MenuItem("기타1", "assets/images/icon_other1.png", () {}),
      _MenuItem("기타2", "assets/images/icon_other2.png", () {}),
      // etc...
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text("메인화면"),
      ),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: menuItems.length,
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3, // 3열
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
        ),
        itemBuilder: (context, index) {
          final item = menuItems[index];
          return InkWell(
            onTap: item.onTap,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // 아이콘 이미지
                Image.asset(item.iconPath, width: 48, height: 48),
                const SizedBox(height: 8),
                Text(item.title),
              ],
            ),
          );
        },
      ),
    );
  }
}

// 내부에서만 쓰는 모델
class _MenuItem {
  final String title;
  final String iconPath;
  final VoidCallback onTap;
  _MenuItem(this.title, this.iconPath, this.onTap);
}

// lib/screens/admin_home_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/auth_provider.dart';
import '../services/admin_api_service.dart'; // 예시
import 'login_screen.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import '../screens/sales_detail_screen.dart';


class AdminHomeScreen extends StatefulWidget {
  const AdminHomeScreen({Key? key}) : super(key: key);

  @override
  _AdminHomeScreenState createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  bool _isLoading = false;
  double _totalMonthlySales = 0.0;
  List<Map<String, dynamic>> _monthlySalesData = []; // 직원별 매출
  List<Map<String, dynamic>> _franchiseOrders = []; // 🔹 프랜차이즈 주문 목록
  int _unreadCount = 0; // 🔹 읽지 않은 주문 개수

  @override
  void initState() {
    super.initState();
    _fetchMonthlySales();
    _initializeFCM(); // FCM 초기화
  }
  Future<void> _initializeFCM() async {
    FirebaseMessaging messaging = FirebaseMessaging.instance;

    // 알림 권한 요청
    NotificationSettings settings = await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // 권한 허용된 경우
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print("✅ 알림 권한 허용됨");

      // 관리자 디바이스 FCM 토큰
      final token = await messaging.getToken();
      print("📲 FCM 토큰(관리자앱): $token");

      // 서버에 FCM 토큰 등록 (optional)
      final user = context.read<AuthProvider>().user; // user is Map<String, dynamic>?
      if (user != null && token != null) {
        await AdminApiService.registerFcmToken(user["id"], token); // 'id' 필드를 배열 인덱스처럼 접근
      }


      // 포그라운드 알림 수신
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        print("📩 [foreground] 알림 수신: ${message.data}");

        // type 분기
        final type = message.data['type'];
        if (type == 'new_sale') {
          final saleIdString = message.data['sale_id'] ?? '0';
          _handleNewSaleForeground(saleIdString);
        }
        else if (type == 'new_franchise_order') {
          // 기존에 있던 프랜차이즈 주문 처리 로직
          _fetchFranchiseOrders();
        }
        else {
          // 기타 알림
          print("기타 알림: $type");
        }
      });

      // 백그라운드/종료 상태에서 알림 클릭 시
      FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
        print("🔔 onMessageOpenedApp: 앱 열림, data=${message.data}");

        final type = message.data['type'];
        if (type == 'new_sale') {
          final saleIdString = message.data['sale_id'] ?? '0';
          final saleId = int.tryParse(saleIdString) ?? 0;
          if (saleId > 0) {
            // 매출 상세 화면으로 이동
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => SalesDetailScreen(saleId: saleId),
              ),
            );
          }
        }
        else if (type == 'new_franchise_order') {
          // 기존 로직 (프랜차이즈 주문 팝업 등)
          _fetchFranchiseOrders();
        }
      });
    }
  }
  void _handleNewSaleForeground(String saleIdString) {
    // 예: foreground에서 Snackbar, 배지 표시 등
    final saleId = int.tryParse(saleIdString) ?? 0;

    // 간단 SnackBar
    ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("새 매출 발생! saleId=$saleId"))
    );

    // 만약 바로 화면 전환할거면 Navigator.push(...) 가능
    // Navigator.push(context, MaterialPageRoute(
    //   builder: (_) => SalesDetailScreen(saleId: saleId),
    // ));
  }

  Future<void> _fetchFranchiseOrders() async {
    // 기존 new_franchise_order 로직
    final employeeId = context.read<AuthProvider>().user?["id"] ?? 0;

    final orders = await AdminApiService.fetchFranchiseOrders(employeeId);
    setState(() {
      _franchiseOrders = orders;
      _unreadCount = orders.where((o) => o['is_read'] == false).length;
    });
  }

  Future<void> _fetchMonthlySales() async {
    setState(() => _isLoading = true);

    final auth = context.read<AuthProvider>();
    final token = auth.token;
    if (token == null) {
      return;
    }

    try {
      // 예시 API:  GET /admin/sales/monthly
      final data = await AdminApiService.fetchMonthlyEmployeeSales(token);
      // 예: data = [{ "employee_id": 1, "employee_name": "홍길동", "total_sales": 2300000 }, ... ]
      double total = data.fold(0.0, (sum, item) => sum + (item["total_sales"] as num).toDouble());
      setState(() {
        _monthlySalesData = List<Map<String, dynamic>>.from(data);
        _totalMonthlySales = total;
      });
    } catch (e) {
      print("❌ 매출 데이터 가져오기 실패: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final adminName = auth.adminUser?["name"] ?? "관리자";

    return Scaffold(
      appBar: AppBar(
        title: Text("관리자 메인 - $adminName"),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              context.read<AuthProvider>().logout();
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
                    (route) => false,
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // ──────────────────────────────────────────
          // 1) 상단부: 버튼들 (ex. GridView)
          // ──────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: _buildTopButtons(),
          ),

          const SizedBox(height: 8),

          // ──────────────────────────────────────────
          // 2) 하단부: 이번 달 직원 매출 순위
          // ──────────────────────────────────────────
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white70,
                borderRadius: BorderRadius.circular(8),
              ),
              margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              padding: const EdgeInsets.all(12),
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _buildMonthlySalesRank(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopButtons() {
    return GridView.count(
      crossAxisCount: 3,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 16,
      crossAxisSpacing: 16,
      children: [
        _buildMenuButton(icon: Icons.people, label: "직원 관리", onTap: () {
          // TODO: 직원관리 화면으로 이동
        }),
        _buildMenuButton(icon: Icons.shopping_cart, label: "판매 정보", onTap: () {
          // TODO: 판매정보 화면으로 이동
        }),
        _buildMenuButton(icon: Icons.list_alt, label: "주문 관리", onTap: () {
          // TODO: 주문관리 화면으로 이동
        }),
        _buildMenuButton(icon: Icons.store, label: "거래처 정보", onTap: () {
          // TODO: 거래처 화면으로 이동
        }),
        _buildMenuButton(icon: Icons.settings, label: "설정", onTap: () {
          // TODO: 설정 화면 이동
        }),
        _buildMenuButton(icon: Icons.analytics, label: "통계 대시보드", onTap: () {
          // TODO: 통계 / 차트 등
        }),
      ],
    );
  }

  Widget _buildMenuButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return ElevatedButton(
      onPressed: onTap,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.all(8),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 32),
          const SizedBox(height: 6),
          Text(label, textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _buildMonthlySalesRank() {
    if (_monthlySalesData.isEmpty) {
      return const Center(child: Text("이번 달 매출 데이터가 없습니다."));
    }

    // 1) 매출액 내림차순 정렬
    final sorted = [..._monthlySalesData];
    sorted.sort((a, b) =>
        (b["total_sales"] as num).compareTo(a["total_sales"] as num)
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "이번 달 직원 매출 순위",
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: ListView.builder(
            itemCount: sorted.length,
            itemBuilder: (_, i) {
              final emp = sorted[i];
              final name = emp["employee_name"] ?? "직원명?";
              final sales = (emp["total_sales"] as num).toDouble();
              final ratio = _totalMonthlySales > 0
                  ? (sales / _totalMonthlySales) * 100
                  : 0.0;
              return ListTile(
                leading: CircleAvatar(child: Text("${i + 1}")), // 순위
                title: Text(name),
                subtitle: Text(
                    "매출: ${NumberFormat("#,###").format(sales)}원 "
                        "(${ratio.toStringAsFixed(1)}%)"
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

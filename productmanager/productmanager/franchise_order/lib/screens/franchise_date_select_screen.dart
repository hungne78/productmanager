import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/auth_provider.dart';
import '../providers/product_provider.dart';
import '../screens/franchise_order_screen.dart';
import '../services/api_service.dart';

class FranchiseDateSelectScreen extends StatefulWidget {
  const FranchiseDateSelectScreen({super.key});

  @override
  State<FranchiseDateSelectScreen> createState() => _FranchiseDateSelectScreenState();
}

class _FranchiseDateSelectScreenState extends State<FranchiseDateSelectScreen> {
  DateTime? serverDate;
  bool isTodayAllowed = false;

  @override
  void initState() {
    super.initState();
    _loadServerTime();
  }

  Future<void> _loadServerTime() async {
    try {
      final now = await ApiService.fetchServerTime();
      final nowTime = TimeOfDay.fromDateTime(now);
      setState(() {
        serverDate = now;
        isTodayAllowed = nowTime.hour < 7;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("서버 시간 불러오기 실패: $e")),
      );
    }
  }

  void _selectDate(DateTime date, int shipmentRound) async {
    final auth = Provider.of<AuthProvider>(context, listen: false);

    // 1️⃣ UI용 그룹 데이터
    final grouped = await ApiService.fetchGroupedByCategoryAndBrand();

    // 2️⃣ 수량 계산용 flat 리스트
    final flat = await ApiService.fetchProductList(auth.clientId!);

    // 3️⃣ Provider에 데이터 저장
    // final grouped = await ApiService.fetchGroupedByCategoryAndBrand();
    final categoryOrder = await ApiService.fetchCategoryOrder();
    final brandOrder = await ApiService.fetchBrandOrder();
    // final flat = grouped.values.expand((b) => b.values.expand((list) => list)).toList();

    final productProvider = Provider.of<ProductProvider>(context, listen: false);
    productProvider.setGroupedCategoryBrand(grouped, categoryOrder, brandOrder);
    await Future.delayed(Duration(milliseconds: 100)); // UI 반영 대기
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => FranchiseOrderScreen(
          selectedDate: date,
          shipmentRound: shipmentRound,
        ),
      ),
    );
  }



  @override
  Widget build(BuildContext context) {
    if (serverDate == null) {
      return const Scaffold(
        backgroundColor: Colors.white,
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final today = serverDate!;
    final tomorrow = today.add(const Duration(days: 1));

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text("주문 날짜 선택"),
        centerTitle: true,
        backgroundColor: Colors.indigo,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const SizedBox(height: 16),
            Text("📅 주문 날짜를 선택해주세요",
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.indigo[800],
                )),
            const SizedBox(height: 24),

            if (isTodayAllowed)
              _buildDateCard(
                context,
                title: "오늘",
                subtitle: _format(today),
                icon: Icons.today,
                color: Colors.indigo,
                onTap: () => _selectDate(today, 1),
              ),
            _buildDateCard(
              context,
              title: "내일",
              subtitle: _format(tomorrow),
              icon: Icons.calendar_today,
              color: Colors.teal,
              onTap: () => _selectDate(tomorrow, 0),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDateCard(BuildContext context,
      {required String title,
        required String subtitle,
        required IconData icon,
        required Color color,
        required VoidCallback onTap}) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: const EdgeInsets.only(bottom: 16),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
        leading: Icon(icon, size: 32, color: color),
        title: Text(
          title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          subtitle,
          style: TextStyle(fontSize: 14, color: Colors.grey[700]),
        ),
        trailing: ElevatedButton(
          onPressed: onTap,
          style: ElevatedButton.styleFrom(
            backgroundColor: color,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          child: const Text("선택"),
        ),
      ),
    );
  }

  String _format(DateTime date) {
    return DateFormat("yyyy-MM-dd (E)", "ko_KR").format(date);
  }
}

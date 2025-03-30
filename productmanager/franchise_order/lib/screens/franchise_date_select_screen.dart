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
        isTodayAllowed = nowTime.hour < 7; // 오전 7시 이전만 오늘 주문 허용
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("서버 시간 불러오기 실패: $e")),
      );
    }
  }

  void _selectDate(DateTime date, int shipmentRound) async {
    final auth = Provider.of<AuthProvider>(context, listen: false);

    // 상품 불러오기
    final products = await ApiService.fetchProductList(auth.clientId!);
    Provider.of<ProductProvider>(context, listen: false).setProducts(products);

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
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final today = serverDate!;
    final tomorrow = today.add(const Duration(days: 1));

    return Scaffold(
      appBar: AppBar(title: const Text("주문 날짜 선택")),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("📆 주문 가능한 날짜를 선택하세요:", style: TextStyle(fontSize: 16)),
            const SizedBox(height: 20),
            if (isTodayAllowed)
              ElevatedButton.icon(
                icon: const Icon(Icons.today),
                label: Text("오늘 (${_format(today)}) - 1차 출고"),
                onPressed: () => _selectDate(today, 1),
              ),
            ElevatedButton.icon(
              icon: const Icon(Icons.calendar_today),
              label: Text("내일 (${_format(tomorrow)}) - 0차 출고"),
              onPressed: () => _selectDate(tomorrow, 0),
            ),
          ],
        ),
      ),
    );
  }

  String _format(DateTime date) {
    return DateFormat("yyyy-MM-dd (E)", "ko_KR").format(date);
  }
}

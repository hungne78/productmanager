// lib/screens/sales/sales_detail_screen.dart

import 'package:flutter/material.dart';
import '../../services/sales_api_service.dart';
import 'package:intl/intl.dart';

class SalesDetailScreen extends StatefulWidget {
  final int saleId;
  const SalesDetailScreen({Key? key, required this.saleId}) : super(key: key);

  @override
  _SalesDetailScreenState createState() => _SalesDetailScreenState();
}

class _SalesDetailScreenState extends State<SalesDetailScreen> {
  bool _isLoading = false;
  Map<String, dynamic>? _sale; // 서버에서 받는 판매 상세 데이터

  @override
  void initState() {
    super.initState();
    _fetchSaleDetail();
  }

  Future<void> _fetchSaleDetail() async {
    setState(() => _isLoading = true);

    try {
      final data = await SalesApiService.fetchSaleDetail(widget.saleId);
      // 예:
      // {
      //   "sale_id":10,
      //   "datetime":"2025-05-01 10:22",
      //   "employee_id":1,"employee_name":"홍길동",
      //   "client_id":99,"client_name":"ABC유통",
      //   "items":[{"product_id":3,"product_name":"사이다","quantity":2,"price":3000},...],
      //   "total_price": 6000,
      //   "incentive": 200,
      //   ...
      // }
      setState(() => _sale = data);
    } catch (e) {
      print("❌ 판매 상세 조회 실패: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("판매 상세 조회 실패: $e")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = NumberFormat("#,###");
    return Scaffold(
      appBar: AppBar(
        title: Text("판매 상세 #${widget.saleId}"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _sale == null
          ? const Center(child: Text("판매 상세 정보를 불러올 수 없습니다."))
          : SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("판매 ID: ${_sale!["sale_id"]}"),
            Text("판매 일시: ${_sale!["datetime"]}"),
            Text("직원: ${_sale!["employee_name"]}"),
            Text("거래처: ${_sale!["client_name"]}"),
            const SizedBox(height: 8),
            // 상품 목록
            Text("📦 판매 상품 목록", style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            ...(_sale!["items"] as List<dynamic>).map((item) {
              final productName = item["product_name"];
              final qty = item["quantity"];
              final price = item["price"];
              return ListTile(
                contentPadding: const EdgeInsets.all(0),
                title: Text(productName ?? "이름 없음"),
                subtitle: Text("수량: $qty, 단가: ${f.format(price)}원"),
              );
            }),
            const Divider(height: 20, thickness: 1),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("총금액: ${f.format(_sale!["total_price"] ?? 0)}원"),
                Text("인센티브: ${f.format(_sale!["incentive"] ?? 0)}원"),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

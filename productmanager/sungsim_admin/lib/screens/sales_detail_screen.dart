// lib/screens/sales_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/sales_api_service.dart'; // 예시

class SalesDetailScreen extends StatefulWidget {
  final int saleId;
  const SalesDetailScreen({Key? key, required this.saleId}) : super(key: key);

  @override
  _SalesDetailScreenState createState() => _SalesDetailScreenState();
}

class _SalesDetailScreenState extends State<SalesDetailScreen> {
  bool _isLoading = false;
  Map<String, dynamic>? _sale;

  @override
  void initState() {
    super.initState();
    _fetchSaleDetail();
  }

  Future<void> _fetchSaleDetail() async {
    setState(() => _isLoading = true);
    try {
      final saleData = await SalesApiService.fetchSaleDetail(widget.saleId);
      setState(() => _sale = saleData);
    } catch (e) {
      print("🚨 매출 상세 조회 실패: $e");
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("매출 상세정보 불러오기 실패")));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = NumberFormat("#,###");
    return Scaffold(
      appBar: AppBar(
        title: Text("매출 상세 #${widget.saleId}"),
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _sale == null
          ? Center(child: Text("매출 정보를 불러올 수 없습니다."))
          : Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("판매 일시: ${_sale!["datetime"]}"),
            Text("담당 직원: ${_sale!["employee_name"] ?? ''}"),
            Text("거래처: ${_sale!["client_name"] ?? ''}"),
            SizedBox(height: 10),
            Text("총 금액: ${f.format(_sale!["total_price"] ?? 0)}원",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            SizedBox(height: 10),
            Text("상품 목록:"),
            ...(_sale!["items"] as List<dynamic>).map((item) {
              return ListTile(
                title: Text(item["product_name"] ?? "상품"),
                subtitle: Text("수량: ${item["quantity"]}, "
                    "합계: ${f.format(item["subtotal"] ?? 0)}원"),
              );
            })
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import '../services/api_service.dart';
import '../auth_provider.dart';

class OrderHistoryScreen extends StatefulWidget {
  final String token;
  final DateTime selectedDate;

  const OrderHistoryScreen({Key? key, required this.token, required this.selectedDate}) : super(key: key);

  @override
  _OrderHistoryScreenState createState() => _OrderHistoryScreenState();
}

class _OrderHistoryScreenState extends State<OrderHistoryScreen> {
  List<Map<String, dynamic>> _orderHistory = [];

  @override
  void initState() {
    super.initState();
    _fetchOrderHistory(widget.selectedDate);
  }
  double _totalAmount = 0;
  double _totalIncentive = 0;
  int _totalBoxes = 0;

  Future<void> _fetchOrderHistory(DateTime selectedDate) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final int employeeId = authProvider.user?.id ?? 0;
    final String formattedDate = selectedDate.toIso8601String().substring(0, 10);

    final response = await ApiService.fetchOrders(widget.token, employeeId, formattedDate);

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = jsonDecode(response.body);

      setState(() {
        _totalAmount = data["total_amount"] ?? 0;
        _totalIncentive = data["total_incentive"] ?? 0;
        _totalBoxes = data["total_boxes"] ?? 0;
        _orderHistory = [];

        for (var order in data["items"]) {
          for (var product in order["products"]) {
            _orderHistory.add({
              'product_name': product['product_name'] ?? "상품 정보 없음",
              'quantity': product['quantity'] ?? 0,
              'category': order['category'] ?? "카테고리 없음",
              'brand_id': order['brand_id']?.toString() ?? "브랜드 없음",
            });
          }
        }
      });


      } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text("주문 목록을 불러오지 못했습니다.")),
            );
          }
  }
  Widget _buildSummaryTable() {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 10, horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey.shade300, width: 1)),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 4,
            offset: Offset(0, -1),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryCell("총 금액", "${_totalAmount.toInt()}원", isBold: true),
          _buildSummaryCell("인센티브", "${_totalIncentive.toInt()}원"),
          _buildSummaryCell("수량", "$_totalBoxes개"),
        ],
      ),
    );
  }


  Widget _buildSummaryCell(String title, String value, {bool isBold = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          title,
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Colors.grey[600]),
        ),
        SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: Colors.black,
          ),
        ),
      ],
    );
  }


  /// 🔹 주문 내역을 표시하는 UI
  Widget _buildOrderHistoryTable() {
    final isFolded = MediaQuery.of(context).size.width < 800; // ✅ 폴드 여부 확인
    final int columns = isFolded ? 6 : 12; // ✅ 화면 크기에 따라 칸 개수 설정

    List<Widget> rows = [];
    Map<String, Map<String, List<Map<String, dynamic>>>> categorizedOrders = {};

    for (var order in _orderHistory) {
      String category = order['category'] ?? "기타";
      String brandId = (order['brand_id'] ?? 0).toString(); // ✅ int → String 변환

      categorizedOrders.putIfAbsent(category, () => {});
      categorizedOrders[category]!.putIfAbsent(brandId, () => []);
      categorizedOrders[category]![brandId]!.add(order);
    }


    categorizedOrders.forEach((category, brands) {
      brands.forEach((brandId, products) { // ✅ brand_id.toString()을 사용하여 오류 방지
        List<Widget> rowChildren = [];

        for (var product in products) {
          if (rowChildren.length >= columns) {
            rows.add(Row(children: rowChildren));
            rowChildren = [];
          }
          rowChildren.add(Expanded(child: _buildOrderCell(product['product_name'])));
          rowChildren.add(Expanded(child: _buildOrderCell(product['quantity'].toString())));
        }

        if (rowChildren.isNotEmpty) {
          rows.add(Row(children: rowChildren));
        }
      });
    });


    return Column(children: rows);
  }

  /// 🔹 주문 내역 셀 디자인
  Widget _buildOrderCell(String text) {
    return Container(
      padding: EdgeInsets.all(8),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade400),
      ),
      child: Text(text, style: TextStyle(fontSize: 12)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        elevation: 2,
        automaticallyImplyLeading: false,
        leading: IconButton(
          icon: Icon(Icons.home, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Center(
          child: Text(
            "주문 내역 (${widget.selectedDate.toLocal().toString().split(' ')[0]})",
            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
          ),
        ),
        actions: [SizedBox(width: 48)], // 타이틀 가운데 맞추기용
      ),
      body: Stack(
        children: [
          Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: _orderHistory.isEmpty
                      ? Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 60),
                      child: Text(
                        "📦 주문 내역이 없습니다.",
                        style: TextStyle(fontSize: 16, color: Colors.grey),
                      ),
                    ),
                  )
                      : Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: _buildOrderHistoryTable(),
                  ),
                ),
              ),
            ],
          ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: _buildSummaryTable(),
          ),
        ],
      ),
    );
  }




}

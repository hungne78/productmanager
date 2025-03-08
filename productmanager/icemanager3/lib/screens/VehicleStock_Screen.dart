import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../vehicle_stock_provider.dart';

class VehicleStockScreen extends StatefulWidget {
  final String token;
  final int employeeId;

  const VehicleStockScreen({Key? key, required this.token, required this.employeeId}) : super(key: key);

  @override
  _VehicleStockScreenState createState() => _VehicleStockScreenState();
}

class _VehicleStockScreenState extends State<VehicleStockScreen> {
  final NumberFormat formatter = NumberFormat("#,###");
  bool _isLoading = true;
  Map<int, int> _stockData = {}; // {상품 ID: 차량 재고}

  @override
  void initState() {
    super.initState();
    _calculateVehicleStock();
  }

  // ✅ 서버에서 주문, 매출 데이터를 가져와 차량 재고 계산
  Future<void> _calculateVehicleStock() async {
    try {
      // ✅ 1. 서버에서 주문한 상품 가져오기
      String selectedDate = DateTime.now().toIso8601String().substring(0, 10); // ✅ 오늘 날짜 기본값
      final orderResponse = await ApiService.fetchOrders(widget.token, widget.employeeId, selectedDate);

      final List<dynamic> orders = jsonDecode(utf8.decode(orderResponse.bodyBytes));

      // ✅ 2. 서버에서 매출 상품 가져오기
      final salesResponse = await ApiService.fetchSales(widget.token, widget.employeeId);
      final List<dynamic> sales = jsonDecode(utf8.decode(salesResponse.bodyBytes));

      // ✅ 3. 전날 차량 재고 가져오기 (Provider에서 가져옴)
      final vehicleStockProvider = Provider.of<VehicleStockProvider>(context, listen: false);
      Map<int, int> stockMap = Map.from(vehicleStockProvider.vehicleStock);

      // ✅ 4. 주문 상품 반영 (추가)
      for (var item in orders) {
        int productId = item['product_id'];
        int orderQuantity = item['order_quantity']; // 주문한 박스 수량
        stockMap[productId] = (stockMap[productId] ?? 0) + orderQuantity;
      }

      // ✅ 5. 매출 상품 반영 (차감)
      for (var item in sales) {
        int productId = item['product_id'];
        int salesQuantity = item['box_count']; // ✅ 박스 단위 수량 계산
        stockMap[productId] = (stockMap[productId] ?? 0) - salesQuantity;
      }

      // ✅ 6. 최신 차량 재고 상태 업데이트 (Provider에 반영)
      vehicleStockProvider.initializeStock(stockMap);

      setState(() {
        _stockData = stockMap;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("차량 재고를 가져오는 데 실패했습니다: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("차량 재고 관리")),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
        child: Column(
          children: [
            DataTable(
              columns: const [
                DataColumn(label: Text('상품 ID', style: TextStyle(fontWeight: FontWeight.bold))),
                DataColumn(label: Text('차량 재고', style: TextStyle(fontWeight: FontWeight.bold))),
              ],
              rows: _stockData.entries.map((entry) {
                final int productId = entry.key;
                final int stockQuantity = entry.value;
                final String formattedStock = formatter.format(stockQuantity);

                return DataRow(
                  cells: [
                    DataCell(Text("$productId")),
                    DataCell(
                      Text(
                        "$formattedStock 박스",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: stockQuantity < 0 ? Colors.red : Colors.black, // ✅ 재고 부족 시 빨간색
                        ),
                      ),
                    ),
                  ],
                );
              }).toList(),
            ),
            const SizedBox(height: 20),

            // ✅ 차량 재고 수동 업데이트 버튼
            ElevatedButton.icon(
              onPressed: _calculateVehicleStock,
              icon: const Icon(Icons.refresh),
              label: const Text("차량 재고 갱신"),
            ),
          ],
        ),
      ),
    );
  }
}

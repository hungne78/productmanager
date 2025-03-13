import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../vehicle_stock_provider.dart';
import 'package:intl/intl.dart'; // ✅ 숫자 포맷을 위한 패키지 추가
class VehicleStockScreen extends StatefulWidget {
  final String token;
  final int employeeId;

  const VehicleStockScreen({Key? key, required this.token, required this.employeeId}) : super(key: key);

  @override
  _VehicleStockScreenState createState() => _VehicleStockScreenState();
}

class _VehicleStockScreenState extends State<VehicleStockScreen> {
  bool _isLoading = true;
  List<Map<String, dynamic>> _stockData = []; // ✅ 데이터 구조 변경 (List<Map<String, dynamic>> 사용)

  @override
  void initState() {
    super.initState();
    _loadVehicleStock(); // ✅ 서버에서 최신 차량 재고 가져오기
  }

  Future<void> _loadVehicleStock() async {
    try {
      final stockData = await ApiService.fetchVehicleStock(widget.token, widget.employeeId);

      setState(() {
        _stockData = stockData;
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

  // ✅ 차량 재고 합계 계산
  int get totalStockQuantity {
    return _stockData.fold<int>(0, (sum, item) => sum + ((item['quantity'] ?? 0) as int));
  }



  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("차량 재고 관리")),
      body: Column(
        children: [
          // ✅ 차량 재고 갱신 버튼 (표 위에 배치)
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: ElevatedButton.icon(
              onPressed: _loadVehicleStock,
              icon: const Icon(Icons.refresh),
              label: const Text("차량 재고 갱신"),
            ),
          ),

          // ✅ 차량 재고 테이블
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade400),
                borderRadius: BorderRadius.circular(8),
                color: Colors.white,
              ),
              child: Column(
                children: [
                  // ✅ 고정된 헤더
                  Container(
                    height: 35,
                    color: Colors.black45,
                    child: _buildHeaderRow(),
                  ),

                  // ✅ 차량 재고 목록 (스크롤 가능)
                  Expanded(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.vertical,
                      child: Column(
                        children: _stockData.map((entry) {
                          return _buildDataRow(entry);
                        }).toList(),
                      ),
                    ),
                  ),

                  // ✅ 차량 재고 합계 (고정)
                  _buildSummaryRow(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  // ✅ 헤더 행 (상품 ID, 상품명, 상품 분류, 차량 재고)
  Widget _buildHeaderRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _buildHeaderCell("상품 ID"),
        _buildHeaderCell("상품명"),
        _buildHeaderCell("상품 분류"),
        _buildHeaderCell("차량 재고"),
      ],
    );
  }

  /// ✅ 데이터 행 (상품 ID, 상품명, 상품 분류, 차량 재고)
  Widget _buildDataRow(Map<String, dynamic> item) {
    final int productId = item['product_id'];
    final String productName = item['product_name'];
    final String category = item['category']; // ✅ 상품 분류 추가
    final int stockQuantity = item['quantity'];

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          bottom: BorderSide(color: Colors.grey.shade300, width: 0.5),
        ),
      ),
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildDataCell("$productId"),
          _buildDataCell(productName),
          _buildDataCell(category), // ✅ 상품 분류 추가
          _buildDataCell("$stockQuantity 박스", isBold: true, isRed: stockQuantity < 0),
        ],
      ),
    );
  }
  final NumberFormat formatter = NumberFormat("#,###");
  // ✅ 차량 재고 합계 (고정)
  Widget _buildSummaryRow() {
    return Container(
      color: Colors.grey.shade300,
      padding: EdgeInsets.symmetric(vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryCell("총 차량 재고", formatter.format(totalStockQuantity) + " 박스", isBold: true),
        ],
      ),
    );
  }

  // ✅ 공통 헤더 셀
  Widget _buildHeaderCell(String text) {
    return Expanded(
      child: Container(
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(vertical: 6),
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  // ✅ 데이터 셀 스타일 적용
  Widget _buildDataCell(String text, {bool isBold = false, bool isRed = false}) {
    return Expanded(
      child: Center(
        child: Text(
          text,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: isRed ? Colors.red : Colors.black87,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  // ✅ 합계 셀 스타일 적용
  Widget _buildSummaryCell(String label, String value, {bool isBold = false}) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            "$label: $value",
            style: TextStyle(
              fontSize: 14,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: isBold ? Colors.black : Colors.black87,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

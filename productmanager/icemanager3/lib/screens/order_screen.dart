import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../product_provider.dart';
import 'package:intl/intl.dart';

class OrderScreen extends StatefulWidget {
  final String token;
  const OrderScreen({Key? key, required this.token}) : super(key: key);

  @override
  _OrderScreenState createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  Map<int, TextEditingController> quantityControllers = {};
  final formatter = NumberFormat("#,###");
  Map<int, FocusNode> focusNodes = {};
  @override
  void initState() {
    super.initState();
  }

  /// 🔹 주문 데이터 서버 전송 (현재는 print()만 수행)
  void _sendOrderToServer() {
    List<Map<String, dynamic>> orderItems = [];

    quantityControllers.forEach((productId, controller) {
      final quantity = int.tryParse(controller.text) ?? 0;
      if (quantity > 0) {
        orderItems.add({
          'product_id': productId,
          'quantity': quantity,
        });
      }
    });

    if (orderItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("주문할 상품을 선택하세요.")),
      );
      return;
    }

    print("📦 주문 데이터 전송: $orderItems");
  }

  double getTotalProductPrice() {
    double total = 0;
    quantityControllers.forEach((productId, controller) {
      int quantity = int.tryParse(controller.text) ?? 0;
      if (quantity > 0) {
        var product = _getProductById(productId);
        double price = ((product['default_price'] ?? 0) * (product['box_quantity'] ?? 1)).toDouble();

        total += price * quantity; // ✅ 상품가격 * 주문수량
      }
    });
    return total;
  }

  double getTotalIncentive() {
    double total = 0;
    quantityControllers.forEach((productId, controller) {
      int quantity = int.tryParse(controller.text) ?? 0;
      if (quantity > 0) {
        var product = _getProductById(productId);
        double incentive = (product['incentive'] ?? 0).toDouble();
        total += incentive * quantity; // ✅ 인센티브 * 주문수량
      }
    });
    return total;
  }

  int getTotalQuantity() {
    int total = 0;
    quantityControllers.forEach((_, controller) {
      total += int.tryParse(controller.text) ?? 0;
    });
    return total; // ✅ 입력한 수량의 총합
  }


  int getTotalVehicleStock() {
    return 0; // ✅ 현재는 모든 차량 재고를 0으로 설정
  }




  /// 🔹 상품 ID로 상품 정보 찾기
  Map<String, dynamic> _getProductById(int productId) {
    final productProvider = context.read<ProductProvider>();
    return productProvider.products.firstWhere((p) => p['id'] == productId, orElse: () => {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("주문 페이지")),
      body: Column(
        children: [
          Expanded(
            child: _buildProductTable(),
          ),
          _buildSummaryRow(), // ✅ 총합 계산을 위한 고정된 행 추가
          ElevatedButton.icon(
            onPressed: _sendOrderToServer,
            icon: const Icon(Icons.send),
            label: const Text("주문 전송"),
          ),
        ],
      ),
    );
  }

  /// 🔹 상품 테이블 UI
  Widget _buildProductTable() {
    final productProvider = context.read<ProductProvider>();
    final products = productProvider.products;

    return Container(
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
            height: 30, // ✅ 세로 크기 줄이기
            color: Colors.black45,
            child: _buildHeaderRow(),
          ),

          // ✅ 상품 목록 (스크롤 가능)
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.vertical,
              child: Column(
                children: products.asMap().entries.map((entry) {
                  int index = entry.key;
                  Map<String, dynamic> product = entry.value;
                  return _buildProductRow(product, index);
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 🔹 테이블 헤더
  Widget _buildHeaderRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _buildHeaderCell("상품명"),
        _buildHeaderCell("상품가격"),
        _buildHeaderCell("인센티브"),
        _buildHeaderCell("차량 재고"),
        _buildHeaderCell("수량 입력"),
      ],
    );
  }

  /// 🔹 개별 상품 행
  Widget _buildProductRow(Map<String, dynamic> product, int index) {
    final productId = product['id'];
    final incentive = product['incentive'] ?? 0;
    final price = (product['default_price'] ?? 0).toDouble();
    final boxQuantity = (product['box_quantity'] ?? 1).toInt();
    final totalPrice = price * boxQuantity; // ✅ 상품가격 = 단가 * 박스당 개수

    quantityControllers.putIfAbsent(productId, () => TextEditingController());

    return Container(
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade300, width: 0.5)),
      ),
      padding: EdgeInsets.symmetric(vertical: 1), // ✅ 세로 간격 줄이기
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildDataCell(product['product_name'], fontSize: 14), // ✅ 상품명
          _buildDataCell(formatter.format(totalPrice), fontSize: 14), // ✅ 상품가격
          _buildDataCell(formatter.format(incentive), fontSize: 14), // ✅ 인센티브
          _buildDataCell("0", fontSize: 14), // ✅ 현재 차량 재고 0
          _buildQuantityInputField(productId, index), // ✅ 인덱스 추가
        ],
      ),
    );
  }



  /// 🔹 합계 표시 행 추가 (버튼 위 고정)
  Widget _buildSummaryRow() {
    return Container(
      color: Colors.grey.shade300,
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          _buildSummaryCell("상품가격 합", "${formatter.format(getTotalProductPrice())} 원"),
          _buildSummaryCell("인센티브 합", "${formatter.format(getTotalIncentive())} 원"),
          _buildSummaryCell("차량 재고 합", "${formatter.format(getTotalVehicleStock())}"),
          _buildSummaryCell("수량 입력 합", "${formatter.format(getTotalQuantity())}"),
        ],
      ),
    );
  }

  /// 🔹 고정 행의 각 셀 디자인을 통일
  Widget _buildSummaryCell(String label, String value) {
    return Expanded(
      child: Center(
        child: Text(
          "$label: $value",
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// 🔹 제목줄 셀 디자인 (폰트 크기 조절)
  Widget _buildHeaderCell(String text) {
    return Expanded(
      child: Container(
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(vertical: 2), // ✅ 세로 간격 줄이기
        child: Text(
          text,
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ),
    );
  }

  /// 🔹 데이터 셀 디자인 (폰트 크기 조절)
  Widget _buildDataCell(String text, {double fontSize = 12}) {
    return Expanded(
      child: Center(
        child: Text(
          text,
          style: TextStyle(fontSize: fontSize),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// 🔹 수량 입력 필드 (폰트 크기 조절)
  /// 🔹 수량 입력 필드 (자동 포커스 이동 추가)
  Widget _buildQuantityInputField(int productId, int index) {
    // ✅ FocusNode 초기화
    focusNodes.putIfAbsent(productId, () => FocusNode());
    quantityControllers.putIfAbsent(productId, () => TextEditingController());

    return Expanded(
      child: TextField(
        controller: quantityControllers[productId],
        focusNode: focusNodes[productId], // ✅ 현재 포커스 적용
        keyboardType: TextInputType.number,
        style: TextStyle(fontSize: 12),
        decoration: InputDecoration(border: OutlineInputBorder()),
        textInputAction: TextInputAction.next, // ✅ 키보드에서 '다음' 버튼 활성화
        onChanged: (value) {
          setState(() {}); // ✅ 입력 값 변경 시 UI 즉시 업데이트
        },
        onEditingComplete: () {
          // ✅ 다음 입력 필드로 포커스 이동
          FocusScope.of(context).nextFocus();
        },
      ),
    );
  }

}

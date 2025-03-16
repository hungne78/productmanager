import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../product_provider.dart';
import '../auth_provider.dart';

class OrderScreen extends StatefulWidget {
  final String token;
  final DateTime selectedDate; // 주문 날짜
  const OrderScreen({Key? key, required this.token, required this.selectedDate}) : super(key: key);

  @override
  _OrderScreenState createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  Map<int, TextEditingController> quantityControllers = {};
  Map<int, FocusNode> focusNodes = {};
  Map<int, int> vehicleStockMap = {}; // ✅ 차량 재고 정보 저장 (product_id → stock)
  final formatter = NumberFormat("#,###");

  @override
  void initState() {
    super.initState();
    _fetchAndSortProducts();
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    _fetchEmployeeVehicleStock(authProvider.user?.id ?? 0); // 🔹 차량 재고 초기화
  }

  // 상품 목록을 서버에서 가져오고 정렬하는 함수
  Future<void> _fetchAndSortProducts() async {
    try {
      final productProvider = context.read<ProductProvider>();
      final List<dynamic> products = await ApiService.fetchAllProducts(widget.token);

      if (products.isNotEmpty) {
        // 활성화된 상품 필터링
        final activeProducts = products.where((product) => product['is_active'] == 1).toList();

        // 분류별로 정렬
        activeProducts.sort((a, b) {
          return a['category'].compareTo(b['category']);
        });

        // 브랜드별로 정렬
        activeProducts.sort((a, b) {
          return a['brand_id'].compareTo(b['brand_id']);
        });

        // 정렬된 상품을 상품 프로바이더에 설정
        productProvider.setProducts(activeProducts);
      } else {
        // 상품 목록이 비어있을 때
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("상품 목록이 비어 있습니다.")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("상품 목록을 가져오는 중 오류 발생: $e")),
      );
    }
  }
  Future<void> _fetchEmployeeVehicleStock(int employeeId) async {
    try {
      final stockList = await ApiService.fetchVehicleStock(widget.token, employeeId);

      setState(() {
        vehicleStockMap = {
          for (var stock in stockList) stock['product_id']: stock['quantity']
        };
      });
    } catch (e) {
      print("🚨 차량 재고 로딩 실패: $e");
      setState(() {
        vehicleStockMap = {};  // Reset in case of failure
      });
    }
  }




  // 서버에 주문을 전송하는 함수
  Future<void> _sendOrderToServer() async {
    if (quantityControllers.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("주문할 상품을 선택하세요.")),
      );
      return;
    }

    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final int employeeId = authProvider.user?.id ?? 0; // 직원 ID
    final String orderDate = widget.selectedDate.toIso8601String().substring(0, 10); // 주문 날짜 (YYYY-MM-DD)

    List<Map<String, dynamic>> orderItems = [];

    quantityControllers.forEach((productId, controller) {
      int quantity = int.tryParse(controller.text) ?? 0;
      if (quantity > 0) {
        var product = _getProductById(productId);
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

    // 서버로 보낼 주문 데이터 구성
    final orderData = {
      "employee_id": employeeId,
      "order_date": orderDate,
      "total_amount": getTotalProductPrice(),
      "total_incentive": getTotalIncentive(),
      "total_boxes": getTotalQuantity(),
      "order_items": orderItems,
    };

    try {
      final response = await ApiService.createOrder(widget.token, orderData);

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("주문이 완료되었습니다!")),
        );
        setState(() {
          quantityControllers.clear(); // 주문 후 입력 필드 초기화
        });
        // ✅ 주문 후 차량 재고 업데이트 호출
        await _fetchEmployeeVehicleStock(employeeId);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("주문종료")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("오류 발생: $e")),
      );
    }
  }

  double getTotalProductPrice() {
    double total = 0;
    quantityControllers.forEach((productId, controller) {
      int quantity = int.tryParse(controller.text) ?? 0;
      if (quantity > 0) {
        var product = _getProductById(productId);
        double price = (product['default_price'] ?? 0).toDouble();
        int boxQuantity = (product['box_quantity'] ?? 1).toInt();
        total += price * boxQuantity * quantity;
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
        total += incentive * quantity;
      }
    });
    return total;
  }

  int getTotalQuantity() {
    int total = 0;
    quantityControllers.forEach((_, controller) {
      total += int.tryParse(controller.text) ?? 0;
    });
    return total;
  }

  // 상품 ID로 상품 정보를 찾는 함수
  Map<String, dynamic> _getProductById(int productId) {
    final productProvider = context.read<ProductProvider>();
    return productProvider.products.firstWhere((p) => p['id'] == productId, orElse: () => {});
  }

  @override
  Widget build(BuildContext context) {
    final productProvider = context.watch<ProductProvider>();

    // 🔹 List<dynamic> → List<Map<String, dynamic>> 변환
    final List<Map<String, dynamic>> products = List<Map<String, dynamic>>.from(productProvider.products);

    return Scaffold(
      appBar: AppBar(title: const Text("주문 페이지")),
      body: Column(
        children: [
          Expanded(
            child: _buildProductTable(products), // 🔹 변환된 리스트 전달
          ),
          _buildSummaryRow(),
          ElevatedButton.icon(
            onPressed: _sendOrderToServer,
            icon: const Icon(Icons.send),
            label: const Text("주문 전송"),
          ),
        ],
      ),
    );
  }

  // 🔹 상품 테이블 UI
  Widget _buildProductTable(List<Map<String, dynamic>> products) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade400),
        borderRadius: BorderRadius.circular(8),
        color: Colors.white,
      ),
      child: Column(
        children: [
          Container(
            height: 30,
            color: Colors.black45,
            child: _buildHeaderRow(),
          ),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.vertical,
              child: Column(
                children: products.map((product) {
                  return _buildProductRow(product);
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }

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

  // 🔹 상품 행 (차량 재고 포함)
  Widget _buildProductRow(Map<String, dynamic> product) {
    final productId = product['id'];
    final price = (product['default_price'] ?? 0).toDouble();
    final incentive = (product['incentive'] ?? 0).toDouble();
    final vehicleStock = vehicleStockMap[productId] ?? 0; // ✅ 차량 재고 가져오기 (없으면 0)

    quantityControllers.putIfAbsent(productId, () => TextEditingController());

    return Container(
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade300, width: 0.5)),
      ),
      padding: EdgeInsets.symmetric(vertical: 1),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildDataCell(product['product_name']),
          _buildDataCell(formatter.format(price)),
          _buildDataCell(formatter.format(incentive)),
          _buildDataCell(formatter.format(vehicleStock)), // ✅ 차량 재고 추가
          _buildQuantityInputField(productId),
        ],
      ),
    );
  }

  Widget _buildDataCell(String text) {
    return Expanded(
      child: Center(
        child: Text(text, style: TextStyle(fontSize: 12), textAlign: TextAlign.center),
      ),
    );
  }

  Widget _buildQuantityInputField(int productId) {
    focusNodes.putIfAbsent(productId, () => FocusNode());
    return Expanded(
      child: TextField(
        controller: quantityControllers[productId],
        focusNode: focusNodes[productId],
        keyboardType: TextInputType.number,
        style: TextStyle(fontSize: 12),
        decoration: InputDecoration(border: OutlineInputBorder()),
        textInputAction: TextInputAction.next,
        onChanged: (value) {
          setState(() {});
        },
        onEditingComplete: () {
          FocusScope.of(context).nextFocus();
        },
      ),
    );
  }

  // 🔹 합계 행 (차량 재고 포함)
  Widget _buildSummaryRow() {
    int totalVehicleStock = vehicleStockMap.values.fold(0, (sum, stock) => sum + stock); // ✅ 차량 재고 합산

    return Container(
      color: Colors.grey.shade300,
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildSummaryCell("상품가격 합", "${formatter.format(getTotalProductPrice())} 원"),
          _buildSummaryCell("인센티브 합", "${formatter.format(getTotalIncentive())} 원"),
          _buildSummaryCell("차량 재고 합", "${formatter.format(totalVehicleStock)}"), // ✅ 추가
          _buildSummaryCell("수량 합계", "${formatter.format(getTotalQuantity())}"),
        ],
      ),
    );
  }
  /// 🔹 제목줄 셀 디자인
  Widget _buildHeaderCell(String text) {
    return Expanded(
      child: Container(
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(vertical: 4), // ✅ 세로 간격 줄이기
        child: Text(text, style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      ),
    );
  }
  Widget _buildSummaryCell(String label, String value) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
          SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black), textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

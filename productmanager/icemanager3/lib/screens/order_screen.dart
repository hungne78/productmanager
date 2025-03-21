import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../product_provider.dart';
import '../auth_provider.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import 'dart:convert';
import 'package:flutter_vibrate/flutter_vibrate.dart';
import 'package:flutter/services.dart';


class OrderScreen extends StatefulWidget {
  final String token;
  final DateTime selectedDate; // 주문 날짜
  const OrderScreen({Key? key, required this.token, required this.selectedDate}) : super(key: key);

  @override
  _OrderScreenState createState() => _OrderScreenState();
}

class _OrderScreenState extends State<OrderScreen> {
  int currentShipmentRound = 0; // ✅ 현재 출고 단계 저장
  int selectedShipmentRound = 1; // ✅ 드롭다운에서 선택된 출고 단계
  List<int> shipmentRounds = List.generate(10, (index) => index + 1); // ✅ 1차 ~ 10차 출고
  late WebSocketChannel channel;
  Map<int, bool> outOfStockItems = {}; // ✅ 재고 부족 품목 추적

  Map<int, TextEditingController> quantityControllers = {};
  Map<int, FocusNode> focusNodes = {};
  Map<int, int> warehouseStockMap = {};
  Map<int, int> vehicleStockMap = {}; // ✅ 차량 재고 정보 저장 (product_id → stock)
  final formatter = NumberFormat("#,###");

  void _connectWebSocket() {
    channel = WebSocketChannel.connect(Uri.parse('ws://your-server.com/ws/stock_updates'));

    channel.stream.listen((message) {
      var data = jsonDecode(message);
      if (data["message"] == "재고 업데이트됨") {
        _fetchWarehouseStock(); // ✅ 실시간 재고 업데이트 반영
      }
    });
  }

  Future<void> _fetchWarehouseStock() async {
    try {
      final stockList = await ApiService.fetchWarehouseStock(widget.token);
      setState(() {
        warehouseStockMap = {for (var stock in stockList) stock['product_id']: stock['quantity']};
      });
    } catch (e) {
      print("🚨 창고 재고 로딩 실패: $e");
    }
  }

  @override
  void initState() {
    super.initState();
    _fetchCurrentShipmentRound(); // ✅ 현재 출고 단계 가져오기
    _fetchAndSortProducts();
    _fetchWarehouseStock();
    _connectWebSocket(); // ✅ WebSocket 연결 추가
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    _fetchEmployeeVehicleStock(authProvider.user?.id ?? 0); // 🔹 차량 재고 초기화
  }


  // ✅ 서버에서 현재 출고 단계를 가져오기
  Future<void> _fetchCurrentShipmentRound() async {
    try {
      final response = await ApiService.getShipmentRound(widget.token, widget.selectedDate);
      if (response.statusCode == 200) {
        final data = response.data;
        setState(() {
          currentShipmentRound = data['shipment_round']; // ✅ 현재 출고 단계 업데이트
          selectedShipmentRound = currentShipmentRound + 1; // ✅ 현재 가능 단계 설정
        });
      } else {
        throw Exception("출고 단계 조회 실패");
      }
    } catch (e) {
      print("🚨 출고 단계 조회 실패: $e");
    }
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

  void _showStockWarning(int productId) async {
    setState(() {
      quantityControllers[productId]?.text = "0"; // ✅ 부족한 경우 0으로 변경
    });

    // ✅ 입력창으로 자동 이동
    FocusScope.of(context).requestFocus(focusNodes[productId]);

    // ✅ UI에서 빨간색으로 변환하여 경고 표시
    Future.delayed(Duration(milliseconds: 100), () {
      setState(() {});
    });
  }


  // 서버에 주문을 전송하는 함수
  Future<void> _sendOrderToServer() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final int employeeId = authProvider.user?.id ?? 0;
    final String orderDate = widget.selectedDate.toIso8601String().substring(0, 10);

    List<Map<String, dynamic>> orderItems = [];
    bool hasStockIssue = false;
    int? firstProblematicProductId;

    setState(() {
      outOfStockItems.clear(); // ✅ 주문 전 부족한 품목 리스트 초기화
    });

    quantityControllers.forEach((productId, controller) {
      int quantity = int.tryParse(controller.text) ?? 0;
      int warehouseStock = warehouseStockMap[productId] ?? 0;

      if (quantity > 0) {
        if (quantity > warehouseStock) {
          hasStockIssue = true;
          firstProblematicProductId ??= productId; // ✅ 첫 번째 부족한 상품 ID 저장
          outOfStockItems[productId] = true; // ✅ 부족한 품목 저장
        } else {
          orderItems.add({'product_id': productId, 'quantity': quantity});
        }
      }
    });

    if (hasStockIssue) {
      setState(() {}); // ✅ UI 갱신 (배경색 & 경고 아이콘 표시)

      FocusScope.of(context).requestFocus(focusNodes[firstProblematicProductId!]); // ✅ 첫 번째 문제 있는 입력칸으로 이동
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("🚨 일부 품목의 재고가 부족합니다. 확인 후 다시 입력하세요."),
          backgroundColor: Colors.red,
        ),
      );

      await _fetchWarehouseStock(); // ✅ 최신 창고 재고 업데이트
      return;
    }

    if (orderItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("주문할 상품을 선택하세요.")),
      );
      return;
    }

    final orderData = {
      "employee_id": employeeId,
      "order_date": orderDate,
      "total_amount": getTotalProductPrice(),
      "total_boxes": getTotalQuantity(),
      "order_items": orderItems,
    };

    try {
      final response = await ApiService.createOrder(widget.token, orderData);
      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("✅ 주문이 완료되었습니다!")),
        );
        setState(() {
          quantityControllers.clear();
        });
        await _fetchWarehouseStock(); // ✅ 주문 후 창고 재고 업데이트
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("❌ 오류 발생: $e")),
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
          // ✅ 현재 출고 단계 표시
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Text(
                  "현재 출고 단계: ${currentShipmentRound + 1}차 출고 대기",
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                LinearProgressIndicator(
                  value: currentShipmentRound / 10, // ✅ 10차 출고 기준 진행률
                  minHeight: 8,
                  backgroundColor: Colors.grey[300],
                  valueColor: const AlwaysStoppedAnimation<Color>(Colors.blue),
                ),
                const SizedBox(height: 8),
                Text(
                  "출고 확정은 PC에서 진행됩니다.",
                  style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                ),
              ],
            ),
          ),

          // ✅ 출고 단계 선택 드롭다운 (현재 출고 가능 단계만 활성화, 비활성 단계는 회색)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: DropdownButton<int>(
              value: selectedShipmentRound,
              onChanged: (int? newValue) {
                if (newValue != null && newValue == currentShipmentRound + 1) {
                  setState(() {
                    selectedShipmentRound = newValue;
                  });
                }
              },
              items: shipmentRounds.map((round) {
                return DropdownMenuItem<int>(
                  value: round,
                  child: Text(
                    "$round차 출고",
                    style: TextStyle(
                      color: round == currentShipmentRound + 1 ? Colors.black : Colors.grey, // ✅ 가능 차수는 검정, 불가능 차수는 회색
                    ),
                  ),
                  enabled: round == currentShipmentRound + 1, // ✅ 현재 가능 차수만 선택 가능
                );
              }).toList(),
            ),
          ),

          Expanded(
            child: _buildProductTable(products), // 🔹 변환된 리스트 전달
          ),
          _buildSummaryRow(),

          // ✅ 주문 전송 버튼 (출고 확정 아님)
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
        _buildHeaderCell("창고재고"),
        _buildHeaderCell("차량재고"),
        _buildHeaderCell("수량입력"),
      ],
    );
  }

  // 🔹 상품 행 (차량 재고 포함)
  Widget _buildProductRow(Map<String, dynamic> product) {
    final productId = product['id'];
    final price = (product['default_price'] ?? 0).toDouble();
    final incentive = (product['incentive'] ?? 0).toDouble();
    final warehouseStock = warehouseStockMap[productId] ?? 0; // ✅ 창고 재고 추가
    final vehicleStock = vehicleStockMap[productId] ?? 0; // ✅ 차량 재고 추가

    // ✅ 수량 입력을 위한 컨트롤러 추가 (초기값 0)
    quantityControllers.putIfAbsent(productId, () => TextEditingController(text: "0"));

    return Container(
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade300, width: 0.5)),
      ),
      padding: EdgeInsets.symmetric(vertical: 8, horizontal: 12), // ✅ 적절한 패딩 추가
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildDataCell(product['product_name']), // ✅ 상품명
          _buildDataCell(formatter.format(price)), // ✅ 가격
          _buildDataCell(formatter.format(incentive)), // ✅ 인센티브
          _buildDataCell(formatter.format(warehouseStock)), // ✅ 창고 재고 추가
          _buildDataCell(formatter.format(vehicleStock)), // ✅ 차량 재고 추가
          _buildQuantityInputField(productId), // ✅ 수량 입력 필드
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
    quantityControllers.putIfAbsent(productId, () => TextEditingController(text: ""));

    bool isOutOfStock = outOfStockItems.containsKey(productId); // ✅ 재고 부족 여부 확인

    return Expanded(
      child: Stack(
        alignment: Alignment.centerRight,
        children: [
          TextField(
            controller: quantityControllers[productId],
            focusNode: focusNodes[productId],
            keyboardType: TextInputType.number,
            textAlign: TextAlign.center,
            decoration: InputDecoration(
              filled: true,
              fillColor: isOutOfStock ? Colors.red.withOpacity(0.2) : Colors.white, // ✅ 부족하면 배경색 변경
              border: OutlineInputBorder(
                borderSide: BorderSide(
                  color: isOutOfStock ? Colors.red : Colors.grey, // ✅ 부족하면 빨간색 테두리
                  width: 2,
                ),
              ),
            ),
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            onTap: () {
              if (quantityControllers[productId]!.text.isEmpty) {
                quantityControllers[productId]!.text = "0";
              }
              quantityControllers[productId]!.selection = TextSelection(
                baseOffset: 0,
                extentOffset: quantityControllers[productId]!.text.length, // ✅ 전체 선택
              );
            },
            onSubmitted: (_) {
              _moveToNextInputField(productId); // ✅ 엔터 누르면 다음 입력칸으로 이동
            },
          ),
          if (isOutOfStock)
            Padding(
              padding: EdgeInsets.only(right: 8),
              child: Icon(Icons.warning, color: Colors.red, size: 18), // ✅ 부족하면 경고 아이콘 표시
            ),
        ],
      ),
    );
  }




  void _moveToNextInputField(int currentProductId) {
    List<int> productIds = quantityControllers.keys.toList(); // ✅ 모든 상품 ID 리스트
    int currentIndex = productIds.indexOf(currentProductId);

    if (currentIndex != -1 && currentIndex < productIds.length - 1) {
      int nextProductId = productIds[currentIndex + 1];

      // ✅ 다음 입력칸으로 이동
      FocusScope.of(context).requestFocus(focusNodes[nextProductId]);

      // ✅ 이동한 입력칸에서 '0' 자동 입력 & 전체 선택
      Future.delayed(Duration(milliseconds: 100), () {
        if (quantityControllers[nextProductId]!.text.isEmpty || quantityControllers[nextProductId]!.text == "0") {
          quantityControllers[nextProductId]!.text = "0";
          quantityControllers[nextProductId]!.selection = TextSelection(
            baseOffset: 0,
            extentOffset: 1, // ✅ 전체 선택 (드래그 효과)
          );
        }
      });
    } else {
      FocusScope.of(context).unfocus(); // ✅ 마지막 칸이면 키보드 닫기
    }
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

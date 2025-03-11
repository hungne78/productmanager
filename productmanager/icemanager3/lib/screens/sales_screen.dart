import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart'; // BLE 라이브러리
import 'package:fluttertoast/fluttertoast.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'dart:developer' as developer;

import '../services/api_service.dart';
import '../auth_provider.dart';
import '../product_provider.dart';
import '../user.dart';
import 'barcode_scanner_page.dart';

/// BLE 스캐너의 Service/Characteristic UUID (실제 기기 정보로 교체)
const String SCANNER_SERVICE_UUID = "00001101-0000-1000-8000-00805F9B34FB";
const String SCANNER_CHARACTERISTIC_UUID = "00001101-0000-1000-8000-00805F9B34FB";

class SalesScreen extends StatefulWidget {
  final String token;
  final Map<String, dynamic> client; // 거래처 정보

  const SalesScreen({Key? key, required this.token, required this.client}) : super(key: key);

  @override
  _SalesScreenState createState() => _SalesScreenState();
}

class _SalesScreenState extends State<SalesScreen> {
  late Map<String, dynamic> client; // 거래처 정보 복사
  late TextEditingController paymentController;
  late FocusNode paymentFocusNode;

  // BLE 스캐너 입력을 받을 숨겨진 TextField (대체 입력용, 일반적으로 사용되지 않음)
  final TextEditingController _scannerController = TextEditingController();
  final FocusNode _scannerFocusNode = FocusNode();

  double totalScannedItemsPrice = 0.0;
  double totalReturnedItemsPrice = 0.0;
  final formatter = NumberFormat("#,###");
  List<Map<String, dynamic>> _scannedItems = []; // 판매 상품 목록
  List<Map<String, dynamic>> _returnedItems = []; // 반품 상품 목록

  bool _isReturnMode = false;
  int? selectedIndex;
  bool _isLoading = false;
  String? _error;
  bool _isScanning = false; // BLE 스캔 상태

  // BLE 관련 변수
  BluetoothDevice? _connectedDevice;
  BluetoothCharacteristic? _barcodeCharacteristic;
  String _bleStatus = "대기 중";

  @override
  void initState() {
    super.initState();
    client = Map<String, dynamic>.from(widget.client);
    paymentController = TextEditingController(text: "");
    paymentFocusNode = FocusNode();

    // ProductProvider에서 상품 목록 업데이트 (없으면 서버에서 재로드)
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final productProvider = context.read<ProductProvider>();
      if (productProvider.products.isEmpty) {
        print("⚠️ SalesScreen: 상품 목록이 비어 있음. 서버에서 다시 불러옴.");
        final List<dynamic> products = await ApiService.fetchAllProducts(widget.token);
        if (products.isNotEmpty) {
          productProvider.setProducts(List<Map<String, dynamic>>.from(products));
          print("✅ SalesScreen: 상품 목록 업데이트 완료. 총 ${products.length}개");
        } else {
          print("❌ SalesScreen: 서버에서 상품을 가져오지 못함.");
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("상품 목록을 가져오지 못했습니다.")),
          );
        }
      } else {
        print("✅ SalesScreen: 이미 ProductProvider에 상품이 있음. 총 ${productProvider.products.length}개");
      }
    });

    // BLE 스캐너 입력 TextField는 읽기 전용으로 설정하여 시스템 키보드가 뜨지 않도록 함.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      FocusScope.of(context).requestFocus(_scannerFocusNode);
    });
  }

  @override
  void dispose() {
    paymentController.dispose();
    paymentFocusNode.dispose();
    _scannerController.dispose();
    _scannerFocusNode.dispose();
    _disconnectBle();
    super.dispose();
  }

  /// TextField onSubmitted 콜백: 엔터 입력 시 바코드 확정
  void _onScannerSubmitted(String value) {
    final cleaned = value.trim();
    print("✅ [onSubmitted] 스캐너 입력값: '$value' → '$cleaned'");
    if (cleaned.isNotEmpty) {
      _handleBarcode(cleaned);
    }
    _scannerController.clear();
    // 포커스 유지
    FocusScope.of(context).requestFocus(_scannerFocusNode);
  }

  /// TextField onChanged 콜백 (디버깅)
  void _onScannerChanged(String value) {
    print("🟡 [onChanged] 현재 TextField 값: '$value'");
  }

  /// BLE 스캔 시작 (정적 메서드 사용)
  Future<void> startBleScan() async {
    setState(() {
      _isScanning = true;
      _bleStatus = "BLE 스캔 중...";
    });
    // BLE 스캔 시작 (타임아웃 5초)
    await FlutterBluePlus.startScan(timeout: const Duration(seconds: 5));
    FlutterBluePlus.scanResults.listen((results) {
      for (ScanResult r in results) {
        print("🔍 [BLE] 발견: ${r.device.name} (${r.device.id}) RSSI: ${r.rssi}");
        // 스캐너 이름을 실제 기기에 맞게 변경 (예: "MyBarcodeScanner")
        if (r.device.name == "MyBarcodeScanner") {
          print("✅ [BLE] 대상 스캐너 찾음: ${r.device.name}");
          FlutterBluePlus.stopScan();
          setState(() {
            _isScanning = false;
          });
          _connectToDevice(r.device);
          break;
        }
      }
    }).onDone(() {
      print("🔴 [BLE] 스캔 완료");
      setState(() {
        _isScanning = false;
        if (_connectedDevice == null) {
          _bleStatus = "스캐너를 찾지 못했습니다.";
        }
      });
    });
  }

  /// BLE 기기에 연결
  Future<void> _connectToDevice(BluetoothDevice device) async {
    try {
      setState(() => _bleStatus = "기기에 연결 중...");
      await device.connect();
      print('✅ [BLE] 연결됨: ${device.name}');
      _connectedDevice = device;
      setState(() => _bleStatus = "${device.name} 연결됨");

      // 서비스/캐릭터리스틱 검색
      List<BluetoothService> services = await device.discoverServices();
      for (var service in services) {
        if (service.uuid.toString().toLowerCase() == SCANNER_SERVICE_UUID) {
          for (var c in service.characteristics) {
            if (c.uuid.toString().toLowerCase() == SCANNER_CHARACTERISTIC_UUID) {
              _barcodeCharacteristic = c;
              print("✅ [BLE] 바코드 캐릭터리스틱 찾음: ${c.uuid}");
              // Notify 활성화
              await c.setNotifyValue(true);
              c.value.listen((value) {
                String scannedData = String.fromCharCodes(value);
                print("🟢 [BLE] 데이터 수신: '$scannedData'");
                _handleBarcode(scannedData.trim());
              });
              break;
            }
          }
        }
      }
    } catch (e) {
      print("🔴 [BLE] 연결 실패: $e");
      setState(() => _bleStatus = "연결 실패: $e");
    }
  }

  /// BLE 기기 연결 해제
  Future<void> _disconnectBle() async {
    if (_connectedDevice != null) {
      try {
        await _connectedDevice!.disconnect();
        print("🔴 [BLE] 연결 해제: ${_connectedDevice!.name}");
      } catch (_) {}
    }
    _connectedDevice = null;
    _barcodeCharacteristic = null;
  }

  // 카메라 스캔 (HID 방식과 별개로 사용)
  Future<String> _scanBarcodeCamera() async {
    try {
      final barcode = await Navigator.push(
        context,
        MaterialPageRoute(builder: (ctx) => const BarcodeScannerPage()),
      );

      if (!mounted) return "";

      if (barcode == null || barcode.isEmpty) {
        setState(() {
          _error = "바코드 스캔이 취소되었습니다.";
        });
        return "";
      } else {
        await _handleBarcode(barcode);
        return barcode; // 스캔된 바코드 값을 반환
      }
    } catch (e) {
      setState(() {
        _error = "카메라 스캔 오류: $e";
      });
      return "";
    }
  }


  // 바코드 처리 (상품 매칭)
  Future<void> _handleBarcode(String barcode) async {
    if (barcode.isEmpty) {
      Fluttertoast.showToast(msg: "스캔된 바코드가 비어 있음");
      return;
    }
    print("🟡 [handleBarcode] 바코드: $barcode");
    setState(() => _isLoading = true);

    try {
      final productProvider = context.read<ProductProvider>();
      if (productProvider.products.isEmpty) {
        Fluttertoast.showToast(msg: "상품 목록이 비어 있습니다.");
        return;
      }
      final productList = productProvider.products.where((p) => p['barcode'] == barcode).toList();
      if (productList.isEmpty) {
        Fluttertoast.showToast(msg: "조회된 상품이 없습니다.");
        return;
      }
      final product = productList.first;
      String productName;
      try {
        productName = utf8.decode(product['product_name'].toString().codeUnits);
      } catch (_) {
        productName = product['product_name'].toString();
      }
      double defaultPrice = (product['default_price'] ?? 0).toDouble();
      bool isProductFixedPrice = product['is_fixed_price'] == true;
      double clientRegularPrice = (widget.client['regular_price'] ?? 0).toDouble();
      double clientFixedPrice = (widget.client['fixed_price'] ?? 0).toDouble();
      double appliedPrice = isProductFixedPrice ? clientFixedPrice : clientRegularPrice;
      String priceType = isProductFixedPrice ? "고정가" : "일반가";

      if (_isReturnMode) {
        int existingIndex = _returnedItems.indexWhere((item) => item['product_id'] == product['id']);
        if (existingIndex >= 0) {
          setState(() {
            _returnedItems[existingIndex]['box_count']++;
          });
        } else {
          setState(() {
            _returnedItems.add({
              'product_id': product['id'],
              'name': productName,
              'box_quantity': product['box_quantity'] ?? 1,
              'box_count': 1,
              'default_price': defaultPrice,
              'client_price': appliedPrice,
              'price_type': priceType,
              'category': product['category'] ?? '',
            });
          });
        }
      } else {
        int existingIndex = _scannedItems.indexWhere((item) => item['product_id'] == product['id']);
        if (existingIndex >= 0) {
          setState(() {
            _scannedItems[existingIndex]['box_count']++;
          });
        } else {
          setState(() {
            _scannedItems.add({
              'product_id': product['id'],
              'name': product['product_name'],
              'box_quantity': product['box_quantity'] ?? 0,
              'box_count': 1,
              'default_price': defaultPrice,
              'client_price': appliedPrice,
              'price_type': priceType,
              'category': product['category'] ?? '',
            });
          });
        }
      }
      Fluttertoast.showToast(msg: "${_isReturnMode ? '반품' : '상품'} 추가됨: $productName");
    } catch (e) {
      print("🔴 [handleBarcode] 오류: $e");
      Fluttertoast.showToast(msg: "스캔 처리 오류: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // UI: 거래처 정보 테이블
  Widget _buildClientInfoTable() {
    return Container(
      padding: const EdgeInsets.all(8.0),
      decoration: BoxDecoration(
        color: Colors.white10,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.indigo),
      ),
      child: Table(
        border: TableBorder.all(color: Colors.blueGrey),
        columnWidths: const {
          0: FractionColumnWidth(0.25),
          1: FractionColumnWidth(0.25),
          2: FractionColumnWidth(0.25),
          3: FractionColumnWidth(0.25),
        },
        children: [
          _buildTableRow("거래처명", widget.client['client_name'],
              "대표자", widget.client['representative_name'] ?? "정보 없음"),
          _buildTableRow("주소", widget.client['address'] ?? "정보 없음",
              "전화번호", widget.client['phone'] ?? "정보 없음"),
          _buildTableRow("사업자 번호", widget.client['business_number'] ?? "정보 없음",
              "이메일", widget.client['email'] ?? "정보 없음"),
          _buildTableRow("일반가",
              widget.client['regular_price']?.toString() ?? "정보 없음",
              "고정가",
              widget.client['fixed_price']?.toString() ?? "정보 없음"),
        ],
      ),
    );
  }

  TableRow _buildTableRow(String title1, String value1, String title2, String value2) {
    return TableRow(children: [
      _buildTableCell(title1, isHeader: true),
      _buildTableCell(value1),
      _buildTableCell(title2, isHeader: true),
      _buildTableCell(value2),
    ]);
  }

  Widget _buildTableCell(String text, {bool isHeader = false, double fontSize = 12}) {
    bool isOverflowing = text.length > 15;
    return GestureDetector(
      onTap: isOverflowing ? () => _showPopup(text) : null,
      child: Padding(
        padding: const EdgeInsets.all(6.0),
        child: Text(
          isOverflowing ? text.substring(0, 15) + "..." : text,
          style: TextStyle(
            fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
            fontSize: fontSize,
          ),
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }

  // UI: 스캔된 상품 테이블 (판매/반품)
  Widget _buildScannedItemsTable() {
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
            height: 35,
            color: Colors.black45,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildHeaderCell("상품명"),
                _buildHeaderCell("개수"),
                _buildHeaderCell("박스수"),
                _buildHeaderCell("가격"),
                _buildHeaderCell("단가"),
                _buildHeaderCell("유형"),
                _buildHeaderCell("합계"),
              ],
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  _buildSaleDataRows(),
                  _buildReturnRows(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderCell(String text) {
    return Expanded(
      child: Container(
        alignment: Alignment.center,
        child: Text(
          text,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  Widget _buildSaleDataRows() {
    return Column(
      children: List.generate(_scannedItems.length, (index) {
        var item = _scannedItems[index];
        bool isFixedPrice = item['price_type'] == "고정가";
        int totalPrice = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price'] * 0.01).round();

        return GestureDetector(
          onTap: () => _selectItem(index),
          child: Container(
            color: index == selectedIndex
                ? Colors.blue.shade100
                : (index.isEven ? Colors.grey.shade100 : Colors.white),
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildDataCell(item['name'].toString()),
                _buildDataCell(item['box_quantity'].toString()),
                _buildDataCell(item['box_count'].toString()),
                _buildDataCell(formatter.format((item['default_price'] ?? 0).round())),
                _buildDataCell((item['client_price'] ?? 0).toStringAsFixed(2)),
                _buildDataCell(isFixedPrice ? '고정가' : '일반가'),
                _buildDataCell(formatter.format(totalPrice), isBold: true),
              ],
            ),
          ),
        );
      }),
    );
  }

  Widget _buildReturnRows() {
    return Column(
      children: List.generate(_returnedItems.length, (index) {
        var item = _returnedItems[index];
        double totalPrice = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price'] * 0.01) * -1;

        return Container(
          color: Colors.red.shade50,
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildDataCell(item['name'].toString(), isRed: true),
              _buildDataCell(item['box_quantity'].toString(), isRed: true),
              _buildDataCell(item['box_count'].toString(), isRed: true),
              _buildDataCell((item['default_price'] ?? 0).toStringAsFixed(2), isRed: true),
              _buildDataCell((item['client_price'] ?? 0).toStringAsFixed(2), isRed: true),
              _buildDataCell(item['price_type'].toString(), isRed: true),
              _buildDataCell(totalPrice.toStringAsFixed(2), isBold: true, isRed: true),
            ],
          ),
        );
      }),
    );
  }

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

  Widget _buildSummaryRow() {
    int totalSalesBoxCount = 0;
    int totalSalesAmount = 0;
    for (var item in _scannedItems) {
      int boxQty = (item['box_quantity'] ?? 0);
      int boxCount = (item['box_count'] ?? 0);
      double defaultPrice = (item['default_price'] ?? 0).toDouble();
      double clientPrice = (item['client_price'] ?? 0).toDouble();
      totalSalesBoxCount += (boxQty * boxCount);
      totalSalesAmount += (boxQty * boxCount * defaultPrice * clientPrice * 0.01).round();
    }
    int totalReturnBoxCount = 0;
    int totalReturnAmount = 0;
    for (var item in _returnedItems) {
      int boxQty = (item['box_quantity'] ?? 0);
      int boxCount = (item['box_count'] ?? 0);
      double defaultPrice = (item['default_price'] ?? 0).toDouble();
      double clientPrice = (item['client_price'] ?? 0).toDouble();
      totalReturnBoxCount += (boxQty * boxCount);
      totalReturnAmount += -1 * (boxQty * boxCount * defaultPrice * clientPrice * 0.01).round();
    }
    int finalTotal = totalSalesAmount + totalReturnAmount;
    totalScannedItemsPrice = finalTotal.toDouble();
    totalReturnedItemsPrice = -totalReturnAmount.toDouble();

    return Container(
      color: Colors.grey.shade300,
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryCell("박스수 합계", formatter.format(totalSalesBoxCount + totalReturnBoxCount)),
          _buildSummaryCell("총 금액", formatter.format(finalTotal) + " 원", isBold: true),
        ],
      ),
    );
  }

  Widget _buildSummaryCell(String label, String value, {bool isBold = false}) {
    return Expanded(
      child: Column(
        children: [
          Text(
            "$label: $value",
            style: TextStyle(
              fontSize: 14,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: isBold ? Colors.black : Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  // 거래처 정보 업데이트 (기존 코드 그대로)
  void _fetchUpdatedClientInfo() async {
    try {
      final response = await ApiService.fetchClientById(widget.token, client['id']);
      if (response.statusCode == 200) {
        var updatedClient = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() {
          client = updatedClient;
        });
      } else {
        throw Exception("거래처 정보 갱신 실패");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("거래처 정보 업데이트 실패: $e")),
      );
    }
  }

  // 수량 수정 다이얼로그
  void _showEditQuantityDialog(int index) {
    TextEditingController quantityController = TextEditingController(
      text: _scannedItems[index]['box_count'].toString(),
    );
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text("수량 수정"),
          content: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.remove),
                onPressed: () {
                  int currentQty = int.tryParse(quantityController.text) ?? 0;
                  if (currentQty > 0) {
                    quantityController.text = (currentQty - 1).toString();
                  }
                },
              ),
              Expanded(
                child: TextField(
                  controller: quantityController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: "수량"),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.add),
                onPressed: () {
                  int currentQty = int.tryParse(quantityController.text) ?? 0;
                  quantityController.text = (currentQty + 1).toString();
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                int newQty = int.tryParse(quantityController.text) ?? 0;
                if (newQty > 0) {
                  setState(() {
                    _scannedItems[index]['box_count'] = newQty;
                  });
                }
                Navigator.pop(ctx);
              },
              child: const Text("수정"),
            ),
          ],
        );
      },
    );
  }

  void _deleteItem(int index) {
    setState(() {
      _scannedItems.removeAt(index);
    });
  }

  void _clearAllItems() {
    setState(() {
      _scannedItems.clear();
      _returnedItems.clear();
    });
    Fluttertoast.showToast(msg: "판매 및 반품 목록이 초기화되었습니다.", gravity: ToastGravity.BOTTOM);
  }
  void _showPopup(String fullText) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("상세 정보"),
          content: Text(fullText),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("닫기"),
            ),
          ],
        );
      },
    );
  }
  void _selectItem(int index) {
    setState(() {
      selectedIndex = index;
    });
  }

  // 반품 스캔
  void _scanReturnItems() async {
    _isReturnMode = true;
    String scannedBarcode = await _scanBarcodeCamera();
    if (scannedBarcode.isNotEmpty) {
      var product = _findProductByBarcode(scannedBarcode);
      if (product != null) {
        setState(() {
          bool isFixedPrice = widget.client['price_type'] == true;
          double unitPrice = isFixedPrice
              ? (product['fixed_price'] ?? 0) * 0.01
              : (product['regular_price'] ?? 0) * 0.01;
          _returnedItems.add({
            'name': product['name'],
            'barcode': scannedBarcode,
            'quantity': 1,
            'unit_price': unitPrice,
            'total_price': -unitPrice,
          });
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("상품을 찾을 수 없습니다.")),
        );
        _isReturnMode = false;
      }
    }
  }

  // 입금 팝업 및 처리
  void _showPaymentDialog() {
    double outstandingAmount = widget.client['outstanding_amount']?.toDouble() ?? 0;
    TextEditingController paymentController = TextEditingController(text: "");
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text("거래처 입금"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text("현재 미수금: ${outstandingAmount.toStringAsFixed(2)} 원"),
              const SizedBox(height: 10),
              TextField(
                controller: paymentController,
                focusNode: paymentFocusNode,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: "입금 금액 입력 (빈 값은 0 처리)",
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                double payAmount = double.tryParse(paymentController.text.trim()) ?? 0;
                if (payAmount < 0) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("올바른 금액을 입력하세요.")),
                  );
                  return;
                }
                _processPayment(payAmount);
                Navigator.of(ctx).pop();
              },
              child: const Text("입금"),
            ),
          ],
        );
      },
    ).then((_) {
      paymentFocusNode.requestFocus();
      _returnedItems.clear();
    });
  }

  void _processPayment(double paymentAmount) async {
    final int clientId = widget.client['id'];
    final String nowStr = DateTime.now().toIso8601String();
    final auth = context.read<AuthProvider>();

    if (paymentAmount < 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("입금 금액은 0 이상이어야 합니다.")),
      );
      return;
    }

    try {
      double updatedOutstandingAmount = widget.client['outstanding_amount'] + totalScannedItemsPrice - paymentAmount;
      setState(() {
        widget.client['outstanding_amount'] = updatedOutstandingAmount;
        client['outstanding_amount'] = updatedOutstandingAmount;
      });

      final response = await ApiService.updateClientOutstanding(
        widget.token,
        widget.client['id'],
        {"outstanding_amount": updatedOutstandingAmount},
      );

      for (var item in _scannedItems) {
        int totalUnits = item['box_quantity'] * item['box_count'];
        double returnAmount = 0.0;
        final payload = {
          "employee_id": auth.user?.id,
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": totalUnits,
          "sale_datetime": nowStr,
          "return_amount": returnAmount,
        };
        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("매출 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }
      for (var item in _returnedItems) {
        int totalUnits = item['box_quantity'] * item['box_count'];
        double defaultPrice = (item['default_price'] ?? 0).toDouble();
        double clientPrice = (item['client_price'] ?? 0).toDouble();
        double returnAmount = (totalUnits * defaultPrice * clientPrice * 0.01).toDouble();
        developer.log("전송 : $totalUnits , $defaultPrice , $clientPrice");
        final payload = {
          "employee_id": auth.user?.id,
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": -totalUnits,
          "sale_datetime": nowStr,
          "return_amount": returnAmount,
        };
        developer.log("📡 반품 데이터 전송: $payload");
        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("반품 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("입금이 성공적으로 처리되었습니다.")),
        );
        setState(() {
          _scannedItems.clear();
          _returnedItems.clear();
        });
      } else {
        throw Exception("서버 오류: ${response.body}");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("입금 처리 중 오류 발생: $e")),
      );
    }
  }

  // 바코드로 상품 찾기
  Map<String, dynamic>? _findProductByBarcode(String barcode) {
    return _scannedItems.firstWhere(
          (product) => product['barcode'] == barcode,
      orElse: () => <String, dynamic>{},
    );
  }

  // 최종 화면 (AppBar에 BLE 스캔 버튼 추가)
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("판매 화면 (BLE 방식)"),
        actions: [
          IconButton(
            icon: const Icon(Icons.bluetooth),
            onPressed: _isScanning ? null : startBleScan,
          ),
        ],
      ),
      body: Column(
        children: [
          // BLE 상태 표시
          Container(
            padding: const EdgeInsets.all(8),
            child: Text("BLE 상태: $_bleStatus"),
          ),
          // 숨겨진 TextField (BLE 스캐너 입력용; readOnly로 키보드 표시 방지)
          TextField(
            controller: _scannerController,
            focusNode: _scannerFocusNode,
            readOnly: true,
            enableInteractiveSelection: false,
            decoration: const InputDecoration(
              border: InputBorder.none,
            ),
            style: const TextStyle(color: Colors.transparent, fontSize: 0.1),
            cursorColor: Colors.transparent,
            onSubmitted: _onScannerSubmitted,
            onChanged: _onScannerChanged,
          ),
          // 거래처 정보
          _buildClientInfoTable(),
          // 스캔된 상품 목록
          Expanded(child: _buildScannedItemsTable()),
          // 합계
          _buildSummaryRow(),
          // 버튼들
          Container(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Wrap(
              spacing: 6,
              runSpacing: 1,
              alignment: WrapAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() => _isReturnMode = false);
                    _scanBarcodeCamera();
                  },
                  icon: const Icon(Icons.camera_alt, size: 20),
                  label: const Text("카메라 스캔", style: TextStyle(fontSize: 14)),
                ),
                ElevatedButton.icon(
                  onPressed: _clearAllItems,
                  icon: const Icon(Icons.clear, size: 18),
                  label: const Text("초기화", style: TextStyle(fontSize: 14)),
                ),
                ElevatedButton.icon(
                  onPressed: selectedIndex == null ? null : () => _showEditQuantityDialog(selectedIndex!),
                  icon: const Icon(Icons.edit, size: 18),
                  label: const Text("수정", style: TextStyle(fontSize: 14)),
                ),
                ElevatedButton.icon(
                  onPressed: selectedIndex == null ? null : () => _deleteItem(selectedIndex!),
                  icon: const Icon(Icons.delete, size: 18),
                  label: const Text("삭제", style: TextStyle(fontSize: 14)),
                ),
                ElevatedButton.icon(
                  onPressed: _showPaymentDialog,
                  icon: const Icon(Icons.save, size: 18),
                  label: const Text("등록", style: TextStyle(fontSize: 14)),
                ),
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() => _isReturnMode = true);
                    _scanBarcodeCamera();
                  },
                  icon: const Icon(Icons.replay),
                  label: const Text("반품", style: TextStyle(fontSize: 14)),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

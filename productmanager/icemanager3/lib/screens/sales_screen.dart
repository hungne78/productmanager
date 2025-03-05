import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';
import '../auth_provider.dart';
import 'barcode_scanner_page.dart';
import '../user.dart';
import 'package:provider/provider.dart';  // ✅ Provider 패키지 추가
import '../product_provider.dart';
import 'package:fluttertoast/fluttertoast.dart';


class SalesScreen extends StatefulWidget {
  final String token;
  final Map<String, dynamic> client; // 거래처 정보

  const SalesScreen({Key? key, required this.token, required this.client})
      : super(key: key);

  @override
  _SalesScreenState createState() => _SalesScreenState();
}


class _SalesScreenState extends State<SalesScreen> {
  List<dynamic> _clients = [];
  dynamic _selectedClient;
  List<Map<String, dynamic>> _scannedItems = []; // 스캔된 품목 리스트

  bool _isLoading = false;
  String? _error;

  void _debugPrintProducts() {
    final productProvider = context.read<ProductProvider>();

    if (productProvider.products.isEmpty) {
      print("❌ 상품 목록이 비어 있습니다! 서버에서 데이터를 받아오지 못했을 가능성이 큽니다.");
    } else {
      print("✅ 상품 목록 로드 완료! 총 ${productProvider.products.length}개의 상품이 있습니다.");
      for (var product in productProvider.products) {
        print("🔹 상품명: ${product['product_name']}, 바코드: ${product['barcode']}");
      }
    }
  }

  @override
  void initState() {
    super.initState();
    // _fetchEmployeeClients(); // 직원이 담당하는 거래처 목록 가져오기
    _selectedClient = widget.client; // ✅ 거래처 정보 설정
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _debugPrintProducts(); // ✅ 상품 목록 디버깅 실행
    });
  }


  // (1) 직원과 연결된 거래처만 가져오기
  // Future<void> _fetchEmployeeClients() async {
  //   setState(() {
  //     _isLoading = true;
  //     _error = null;
  //   });
  //
  //   try {
  //     final resp = await ApiService.fetchEmployeeClients(widget.token, widget.employeeId);
  //     if (resp.statusCode == 200) {
  //       final data = jsonDecode(resp.body) as List;
  //       setState(() {
  //         _clients = data;
  //       });
  //     } else {
  //       setState(() {
  //         _error = "거래처 조회 실패: ${resp.statusCode}\n${resp.body}";
  //       });
  //     }
  //   } catch (e) {
  //     setState(() {
  //       _error = "오류: $e";
  //     });
  //   } finally {
  //     setState(() {
  //       _isLoading = false;
  //     });
  //   }
  // }

  // 바코드 카메라 스캔
  Future<void> _scanBarcodeCamera() async {
    try {
      final barcode = await Navigator.push(
        context,
        MaterialPageRoute(builder: (ctx) => const BarcodeScannerPage()),
      );
      if (!mounted) return;
      if (barcode == null || barcode.isEmpty) {
        setState(() {
          _error = "바코드 스캔이 취소되었습니다.";
        });
      } else {
        await _handleBarcode(barcode);
      }
    } catch (e) {
      setState(() {
        _error = "카메라 스캔 오류: $e";
      });
    }
  }

  // 바코드 처리
  Future<void> _handleBarcode(String barcode) async {

    if (barcode.isEmpty) {
      Fluttertoast.showToast(msg: "스캔된 바코드가 비어 있습니다.", gravity: ToastGravity.BOTTOM);
      return;
    }

    setState(() => _isLoading = true);

    try {
      final productProvider = context.read<ProductProvider>();

      if (productProvider.products.isEmpty) {
        print("❌ 상품 목록이 비어 있음! 상품 데이터를 불러오지 못함.");
        Fluttertoast.showToast(msg: "상품 목록이 비어 있습니다. 먼저 상품을 다운로드하세요.", gravity: ToastGravity.BOTTOM);
        return;
      }

      print("🔍 스캔된 바코드: $barcode");
      final product = productProvider.products.firstWhere(
            (p) => p['barcode'] == barcode,
        orElse: () => null,
      );

      if (product == null) {
        print("❌ 스캔된 바코드와 일치하는 상품 없음: $barcode");
        Fluttertoast.showToast(msg: "조회된 상품이 없습니다.", gravity: ToastGravity.BOTTOM);
        return;
      }

      print("✅ 상품 확인됨: ${product['product_name']}");
      Fluttertoast.showToast(msg: "상품 추가됨: ${product['product_name']}", gravity: ToastGravity.BOTTOM);

      final appliedPrice = product['default_price'].toDouble();
      final existingIndex = _scannedItems.indexWhere(
            (item) => item['product_id'] == product['id'],
      );

      if (existingIndex >= 0) {
        setState(() {
          _scannedItems[existingIndex]['box_count']++;
        });
      } else {
        setState(() {
          _scannedItems.add({
            'product_id': product['id'],
            'name': product['product_name'],
            'default_price': product['default_price'].toDouble(),
            'client_price': appliedPrice,
            'box_quantity': product['box_quantity'] ?? 0,
            'box_count': 1,
            'category': product['category'] ?? '',
          });
        });
      }
    } catch (e) {
      Fluttertoast.showToast(msg: "스캔 처리 오류: $e", gravity: ToastGravity.BOTTOM);
    } finally {
      setState(() => _isLoading = false);
    }
  }



  // (2) 인쇄(매출 등록) 버튼
  Future<void> _postSales() async {
    if (_scannedItems.isEmpty) {
      Fluttertoast.showToast(msg: "스캔된 상품이 없습니다.", gravity: ToastGravity.BOTTOM);
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final int clientId = widget.client['id'];
      final String today = DateTime.now().toIso8601String().substring(0, 10);
      final auth = context.read<AuthProvider>();

      double totalSalesAmount = 0.0; // 총 판매 금액

      for (var item in _scannedItems) {
        final int totalUnits = item['box_quantity'] * item['box_count'];
        final double totalAmount = totalUnits * (item['client_price'] as num).toDouble(); // ✅ num → double 변환
        totalSalesAmount += totalAmount;

        final payload = {
          "employee_id": auth.user?.id, // ✅ 직원 ID 포함
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": totalUnits,
          "sale_datetime": DateTime.now().toIso8601String(), // ✅ `sale_datetime` 필드 추가 및 ISO 8601 형식 변환
        };

        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("매출 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }

      // ✅ 미수금 업데이트 요청
      final newOutstandingAmount = widget.client['outstanding_amount'] + totalSalesAmount;
      final updatePayload = {
        "outstanding_amount": newOutstandingAmount,
      };

      final outstandingResp = await ApiService.updateClientOutstanding(widget.token, clientId, updatePayload);
      if (outstandingResp.statusCode != 200) {
        throw Exception("미수금 업데이트 실패: ${outstandingResp.statusCode} / ${outstandingResp.body}");
      }

      // ✅ 성공 메시지 출력 & 목록 초기화
      setState(() {
        _scannedItems.clear();
        widget.client['outstanding_amount'] = newOutstandingAmount;
      });

      Fluttertoast.showToast(msg: "매출 등록 완료!", gravity: ToastGravity.BOTTOM);

    } catch (e) {
      Fluttertoast.showToast(msg: "매출 등록 오류: $e", gravity: ToastGravity.BOTTOM);
    } finally {
      setState(() => _isLoading = false);
    }
  }


  double get totalAmount {
    double sum = 0;
    for (var item in _scannedItems) {
      sum += (item['box_count'] * item['box_quantity'] * item['client_price']);
    }
    return sum;
  }
  Widget _buildClientInfoTable() {
    return Container(
      padding: const EdgeInsets.all(8.0),
      decoration: BoxDecoration(
        color: Colors.blue.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue),
      ),
      child: Table(
        border: TableBorder.all(color: Colors.blueAccent),
        columnWidths: const {
          0: FractionColumnWidth(0.25),
          1: FractionColumnWidth(0.25),
          2: FractionColumnWidth(0.25),
          3: FractionColumnWidth(0.25),
        },
        children: [
          _buildTableRow("거래처명", widget.client['client_name'], "미수금", "${widget.client['outstanding_amount']} 원"),
          _buildTableRow("주소", widget.client['address'] ?? "정보 없음", "전화번호", widget.client['phone'] ?? "정보 없음"),
          _buildTableRow("사업자 번호", widget.client['business_number'] ?? "정보 없음", "이메일", widget.client['email'] ?? "정보 없음"),
          _buildTableRow("일반가", widget.client['regular_price']?.toString() ?? "정보 없음", "고정가", widget.client['fixed_price']?.toString() ?? "정보 없음"),
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

  Widget _buildTableCell(String text, {bool isHeader = false}) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Text(
        text,
        style: TextStyle(
          fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
          fontSize: isHeader ? 16 : 14,
        ),
      ),
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("판매 화면")),
      body: Column(
        children: [
          // ✅ 거래처 정보 (화면의 1/4 크기)
          SizedBox(
            height: MediaQuery.of(context).size.height * 0.25,
            child: _buildClientInfoTable(),
          ),

          // ✅ 스캔된 상품 목록
          Expanded(
            child: DataTable(
              columns: const [
                DataColumn(label: Text('상품명')),
                DataColumn(label: Text('박스 갯수')),
                DataColumn(label: Text('단가')),
                DataColumn(label: Text('합계')),
              ],
              rows: _scannedItems.map((item) {
                final double total = item['box_count'] * item['client_price'];
                return DataRow(cells: [
                  DataCell(Text(item['name'].toString())),
                  DataCell(Text(item['box_count'].toString())),
                  DataCell(Text(item['client_price'].toStringAsFixed(0))),
                  DataCell(Text(total.toStringAsFixed(0))),
                ]);
              }).toList(),
            ),
          ),

          ElevatedButton.icon(
            onPressed: _scanBarcodeCamera,
            icon: const Icon(Icons.camera_alt),
            label: const Text("스캔"),
          ),
          ElevatedButton.icon(
            onPressed: _postSales,
            icon: const Icon(Icons.save),
            label: const Text("등록"),
          ),

        ],
      ),
    );
  }


}

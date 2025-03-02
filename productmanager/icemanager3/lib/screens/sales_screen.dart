import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';
import 'barcode_scanner_page.dart';

class SalesScreen extends StatefulWidget {
  final String token;
  final int employeeId; // 로그인한 직원 ID(영업사원 PK)

  const SalesScreen({
    Key? key,
    required this.token,
    required this.employeeId, // 꼭 전달받도록
  }) : super(key: key);

  @override
  State<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends State<SalesScreen> {
  List<dynamic> _clients = [];
  dynamic _selectedClient;

  // 스캔된 품목(박스 갯수 등)
  List<Map<String, dynamic>> _scannedItems = [];

  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchEmployeeClients(); // 직원 전담 거래처만 불러오기
  }

  // (1) 직원과 연결된 거래처만 가져오기
  Future<void> _fetchEmployeeClients() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      // 새로 만든(or 기존) API. 예: GET /employees/{employee_id}/clients
      // → return: [ {id, client_name, ...}, ... ]
      final resp = await ApiService.fetchEmployeeClients(widget.token, widget.employeeId);
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as List;
        setState(() {
          _clients = data;
        });
      } else {
        setState(() {
          _error = "거래처 조회 실패: ${resp.statusCode}\n${resp.body}";
        });
      }
    } catch (e) {
      setState(() {
        _error = "오류: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

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
    if (_selectedClient == null) {
      setState(() {
        _error = "거래처를 먼저 선택하세요.";
      });
      return;
    }
    setState(() => _isLoading = true);
    try {
      final productResp = await ApiService.fetchProductByBarcode(widget.token, barcode);
      if (productResp.statusCode != 200) {
        setState(() {
          _error = "상품 조회 실패: ${productResp.statusCode}";
        });
        return;
      }
      final productData = jsonDecode(productResp.body);

      // 거래처 단가 조회
      final priceResp = await ApiService.fetchClientPrice(
        widget.token,
        _selectedClient['id'],
        productData['id'],
      );
      double appliedPrice;
      if (priceResp.statusCode == 200) {
        final priceData = jsonDecode(priceResp.body);
        appliedPrice = priceData['special_price']?.toDouble() ?? productData['default_price'].toDouble();
      } else if (priceResp.statusCode == 404) {
        appliedPrice = productData['default_price']?.toDouble() ?? 0;
      } else {
        setState(() {
          _error = "단가 조회 실패: ${priceResp.statusCode}";
        });
        return;
      }

      final existingIndex = _scannedItems.indexWhere(
            (item) => item['product_id'] == productData['id'],
      );
      if (existingIndex >= 0) {
        // 이미 있는 항목이면 박스 갯수만 1 증가
        _scannedItems[existingIndex]['box_count']++;
      } else {
        _scannedItems.add({
          'product_id': productData['id'],
          'name': productData['product_name'],
          'default_price': productData['default_price']?.toDouble() ?? 0,
          'client_price': appliedPrice,
          'box_quantity': productData['box_quantity'] ?? 0,
          'box_count': 1,
          'category': productData['category'] ?? '',
        });
      }
      setState(() {});
    } catch (e) {
      setState(() {
        _error = "스캔 처리 오류: $e";
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // (2) 인쇄(또는 “등록”) 버튼 누르면, 스캔된 항목을 서버에 매출로 등록
  Future<void> _postSales() async {
    if (_selectedClient == null) {
      setState(() {
        _error = "거래처를 선택하세요.";
      });
      return;
    }
    if (_scannedItems.isEmpty) {
      setState(() {
        _error = "스캔된 상품이 없습니다.";
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final int clientId = _selectedClient['id'];
      final String today = DateTime.now().toIso8601String().substring(0, 10);
      // 예: "2025-03-30"

      // 스캔 아이템을 각각 POST /sales (단건)으로 등록하는 예
      // (원한다면 /orders 등에 한번에 등록할 수도 있음)
      for (var item in _scannedItems) {
        final int totalUnits = item['box_quantity'] * item['box_count'];
        final payload = {
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": totalUnits, // 박스갯수 × 박스당개수
          "sale_date": today,
        };
        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("매출 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }

      // 성공적으로 등록했다면 안내
      setState(() {
        _scannedItems.clear(); // 전송 후 목록 비우기
        _error = "매출 등록 완료!";
      });
    } catch (e) {
      setState(() {
        _error = "매출 전송 오류: $e";
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // 합계(금액) 로직: box_count * box_quantity * client_price
  double get totalAmount {
    double sum = 0;
    for (var item in _scannedItems) {
      sum += (item['box_count'] * item['box_quantity'] * item['client_price']);
    }
    return sum;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("판매 화면"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
        children: [
          // 오류 메시지
          if (_error != null)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Text(_error!, style: const TextStyle(color: Colors.red)),
            ),
          // 거래처 선택 (영업사원과 관계있는 거래처만)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: DropdownButton<dynamic>(
              hint: const Text("거래처 선택"),
              value: _selectedClient,
              isExpanded: true,
              items: _clients.map((c) {
                return DropdownMenuItem(
                  value: c,
                  child: Text("${c['client_name']} (미수금: ${c['outstanding_amount']})"),
                );
              }).toList(),
              onChanged: (val) {
                setState(() {
                  _selectedClient = val;
                });
              },
            ),
          ),
          // 스캔 리스트
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('상품명')),
                  DataColumn(label: Text('박스당개수')),
                  DataColumn(label: Text('박스 갯수')),
                  DataColumn(label: Text('단가')),
                  DataColumn(label: Text('합계')),
                ],
                rows: _scannedItems.map((item) {
                  final int bq = item['box_quantity'];
                  final int bc = item['box_count'];
                  final double cp = item['client_price'];
                  final total = bq * bc * cp;
                  return DataRow(cells: [
                    DataCell(Text(item['name'].toString())),
                    DataCell(Text(bq.toString())),
                    DataCell(Text(bc.toString())),
                    DataCell(Text(cp.toStringAsFixed(0))),
                    DataCell(Text(total.toStringAsFixed(0))),
                  ]);
                }).toList(),
              ),
            ),
          ),
          // 합계
          Container(
            padding: const EdgeInsets.all(8),
            color: Colors.grey.shade300,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Text(
                  "총합: ${totalAmount.toStringAsFixed(0)} 원",
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
          // 버튼들: 카메라 스캔, 인쇄(매출등록)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton.icon(
                onPressed: _scanBarcodeCamera,
                icon: const Icon(Icons.camera_alt),
                label: const Text("스캔"),
              ),
              ElevatedButton.icon(
                onPressed: _postSales, // 인쇄=매출 등록
                icon: const Icon(Icons.print),
                label: const Text("인쇄(등록)"),
              ),
            ],
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

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
import 'package:intl/intl.dart'; // ✅ 숫자 포맷을 위한 패키지 추가

class SalesScreen extends StatefulWidget {
  final String token;
  final Map<String, dynamic> client; // 거래처 정보

  const SalesScreen({Key? key, required this.token, required this.client}) : super(key: key);

  @override
  _SalesScreenState createState() => _SalesScreenState();
}


class _SalesScreenState extends State<SalesScreen> {
  late Map<String, dynamic> client; // ✅ 변경 가능하도록 설정
  late TextEditingController paymentController;
  late FocusNode paymentFocusNode;
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>(); // ✅ GlobalKey 추가
  double totalScannedItemsPrice = 0.0;
  double totalReturnedItemsPrice = 0.0;
  final formatter = NumberFormat("#,###"); // ✅ 천단위 콤마 포맷 설정
  List<Map<String, dynamic>> _returnedItems = []; // ✅ 반품 상품 리스트

  bool _isReturnMode = false; // ✅ 기본값: 판매 모드 (반품 모드가 아님)

  dynamic _selectedClient;
  List<Map<String, dynamic>> _scannedItems = []; // 스캔된 품목 리스트
  int? selectedIndex; // ✅ 선택된 행의 인덱스 저장
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
    client = Map<String, dynamic>.from(widget.client); // `client` 초기화
    paymentController = TextEditingController(text: ""); // 입금 금액 기본값 빈 문자열로 설정
    paymentFocusNode = FocusNode(); // 포커스 노드 초기화
    _selectedClient = widget.client; // 거래처 정보 설정

  }
  @override
  void dispose() {
    paymentController.dispose();
    paymentFocusNode.dispose();
    super.dispose();
  }
  // 상품을 클릭하여 선택된 인덱스를 저장
  void _selectItem(int index) {
    setState(() {
      selectedIndex = index; // 선택된 상품의 인덱스를 저장
    });
  }
  // 바코드 카메라 스캔
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
        return ""; // ✅ 빈 문자열 반환 (예외 처리)
      } else {
        await _handleBarcode(barcode);
        return barcode; // ✅ 스캔된 바코드 값 반환
      }
    } catch (e) {
      setState(() {
        _error = "카메라 스캔 오류: $e";
      });
      return ""; // ✅ 오류 발생 시 빈 값 반환
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
        Fluttertoast.showToast(msg: "상품 목록이 비어 있습니다. 먼저 상품을 다운로드하세요.", gravity: ToastGravity.BOTTOM);
        return;
      }

      final product = productProvider.products.firstWhere(
            (p) => p['barcode'] == barcode,
        orElse: () => null,
      );

      if (product == null) {
        Fluttertoast.showToast(msg: "조회된 상품이 없습니다.", gravity: ToastGravity.BOTTOM);
        return;
      }
      // ✅ UTF-8 디코딩 예외 처리
      String productName;
      try {
        productName = utf8.decode(product['product_name'].toString().codeUnits);
      } catch (e) {
        print("❌ 상품명 UTF-8 디코딩 오류: $e");
        productName = product['product_name'].toString(); // 오류 발생 시 원본 그대로 사용
      }

      // ✅ 상품의 원래 가격 (기본 가격)
      double defaultPrice = (product['default_price'] ?? 0).toDouble();

      // ✅ 상품이 고정가인지 일반가인지 판별
      bool isProductFixedPrice = product['is_fixed_price'] == true; // 상품 자체의 가격 유형 확인

      // ✅ 거래처 단가 적용
      double clientRegularPrice = (widget.client['regular_price'] ?? 0).toDouble();
      double clientFixedPrice = (widget.client['fixed_price'] ?? 0).toDouble();
      double appliedPrice = isProductFixedPrice ? clientFixedPrice : clientRegularPrice; // ✅ 상품 가격 유형에 따라 거래처 가격 적용
      String priceType = isProductFixedPrice ? "고정가" : "일반가";

      if (_isReturnMode) {
        // ✅ 반품 모드
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
              'box_quantity': 1, // ✅ 박스수 1 고정
              'box_count': 1, // ✅ 개수 기본 1
              'default_price': defaultPrice, // ✅ 상품의 원래 가격 (기본 가격)
              'client_price': appliedPrice, // ✅ 거래처 적용 단가
              'price_type': priceType, // ✅ 가격 유형 (일반가 / 고정가)
              'category': product['category'] ?? '',
            });
          });
        }
      } else {
        // ✅ 일반 판매 모드
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
              'default_price': defaultPrice, // ✅ 상품의 원래 가격 (기본 가격)
              'client_price': appliedPrice, // ✅ 거래처 적용 단가
              'price_type': priceType, // ✅ 가격 유형 (일반가 / 고정가)
              'category': product['category'] ?? '',
            });
          });
        }
      }

      Fluttertoast.showToast(
        msg: "${_isReturnMode ? '반품' : '상품'} 추가됨: ${product['product_name']}",
        gravity: ToastGravity.BOTTOM,
      );
    } catch (e) {
      Fluttertoast.showToast(msg: "스캔 처리 오류: $e", gravity: ToastGravity.BOTTOM);
    } finally {
      setState(() => _isLoading = false);
    }
  }

//거래처정보테이블
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
          _buildTableRow("거래처명", widget.client['client_name'], "미수금", "${formatter.format(widget.client['outstanding_amount'])} 원"),
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

  Widget _buildTableCell(String text, {bool isHeader = false, double fontSize = 12}) {
    bool isOverflowing = text.length > 15; // 15자 이상이면 생략 처리
    return GestureDetector(
      onTap: isOverflowing ? () => _showPopup(text) : null,
      child: Padding(
        padding: const EdgeInsets.all(6.0),
        child: Text(
          isOverflowing ? text.substring(0, 15) + "..." : text, // 15자 초과 시 생략
          style: TextStyle(
            fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
            fontSize: fontSize, // ✅ 폰트 크기 조정
          ),
          overflow: TextOverflow.ellipsis, // ✅ 너무 길면 '...' 처리
        ),
      ),
    );
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("판매 화면")),
      body: Column(
        children: [
          // ✅ 거래처 정보 테이블 (최소 크기 유지)
          _buildClientInfoTable(),

          // ✅ 스캔된 상품 목록 (버튼 위까지 꽉 차도록 확장)
          Expanded(
            child: _buildScannedItemsTable(),
          ),

          // ✅ 하단 합계 (고정)
          _buildSummaryRow(),

          // ✅ 버튼 (하단 고정)
          Container(
            padding: EdgeInsets.symmetric(vertical: 2), // ✅ 위아래 여백 줄이기
            child: Wrap(
              spacing: 6, // ✅ 버튼 간 가로 간격 줄이기
              runSpacing: 1, // ✅ 버튼 줄바꿈 간격 줄이기
              alignment: WrapAlignment.center, // ✅ 버튼들을 중앙 정렬
              children: [
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() {
                      _isReturnMode = false; // ✅ 반품 모드 해제
                    });
                    _scanBarcodeCamera();
                  },
                  icon: Icon(Icons.camera_alt, size: 20), // ✅ 아이콘 크기 조정
                  label: Text("스캔", style: TextStyle(fontSize: 14)), // ✅ 텍스트 크기 조정
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size(60, 30), // ✅ 버튼 크기 조정 (너비, 높이)
                    padding: EdgeInsets.symmetric(horizontal: 8), // ✅ 내부 여백 조정
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: _clearAllItems,
                  icon: Icon(Icons.clear, size: 18),
                  label: Text("초기화", style: TextStyle(fontSize: 14)),
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size(60, 30),
                    padding: EdgeInsets.symmetric(horizontal: 8),
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: selectedIndex == null ? null : () => _showEditQuantityDialog(selectedIndex!),
                  icon: Icon(Icons.edit, size: 18),
                  label: Text("수정", style: TextStyle(fontSize: 14)),
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size(60, 30),
                    padding: EdgeInsets.symmetric(horizontal: 8),
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: selectedIndex == null ? null : () => _deleteItem(selectedIndex!),
                  icon: Icon(Icons.delete, size: 18),
                  label: Text("삭제", style: TextStyle(fontSize: 14)),
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size(60, 30),
                    padding: EdgeInsets.symmetric(horizontal: 8),
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: () => _showPaymentDialog(),
                  icon: Icon(Icons.save, size: 18),
                  label: Text("등록", style: TextStyle(fontSize: 14)),
                  style: ElevatedButton.styleFrom(
                    minimumSize: Size(60, 30),
                    padding: EdgeInsets.symmetric(horizontal: 8),
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() {
                      _isReturnMode = true; // ✅ 반품 모드 활성화
                    });
                    _scanBarcodeCamera(); // ✅ 스캔 실행
                  },
                  icon: Icon(Icons.replay),
                  label: Text("반품"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent, // ✅ 반품 버튼 빨간색
                  ),
                ),


              ],
            ),
          )
        ],
      ),
    );
  }

  void _scanReturnItems() async {
    _isReturnMode = true; // ✅ 반품 모드 활성화
    // ✅ 카메라 스캔 실행 후 바코드 값 가져오기
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
            'quantity': 1, // ✅ 바코드 찍는 숫자 (낱개)
            'unit_price': unitPrice, // ✅ 단가 (일반가 or 고정가)
            'total_price': -unitPrice, // ✅ 반품 금액 (빨간색, 마이너스 값)
          });
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("상품을 찾을 수 없습니다.")),
        );
        _isReturnMode = false; // ✅ 반품 모드 종료
      }
    }
  }

  
  //입금 팝업창
  void _showPaymentDialog() {
    double outstandingAmount = widget.client['outstanding_amount']?.toDouble() ?? 0;
    TextEditingController paymentController = TextEditingController(text: "");

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("거래처 입금"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text("현재 미수금: ${outstandingAmount.toStringAsFixed(2)} 원"),
              SizedBox(height: 10),
              TextField(
                controller: paymentController,
                focusNode: paymentFocusNode,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: "입금 금액 입력 (빈 값은 0 처리)",
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                // ✅ 입력값이 없으면 0으로 처리
                double paymentAmount = double.tryParse(paymentController.text.trim()) ?? 0;

                if (paymentAmount < 0) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("올바른 금액을 입력하세요.")),
                  );
                  return;
                }

                _processPayment(paymentAmount); // ✅ double 값 전달
                Navigator.of(context).pop(); // ✅ 팝업 닫기
              },
              child: Text("입금"),
            ),
          ],
        );
      },
    ).then((_) {
      paymentFocusNode.requestFocus(); // ✅ 포커스 유지
      _returnedItems.clear();
    });
  }





  //미수금 차감 및 서버 전송
  void _processPayment(double paymentAmount) async {
    final int clientId = widget.client['id'];
    final String nowStr = DateTime.now().toIso8601String();
    final auth = context.read<AuthProvider>();

    if (paymentAmount < 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("입금 금액은 0 이상이어야 합니다.")),
      );
      return;
    }

    try {
      // ✅ 미수금 = 기존 미수금 + 스캔한 상품 가격 - 입금액
      double updatedOutstandingAmount = widget.client['outstanding_amount'] + totalScannedItemsPrice - paymentAmount;

      // ✅ UI 업데이트
      setState(() {
        widget.client['outstanding_amount'] = updatedOutstandingAmount; // ✅ 위젯 값 변경
        client['outstanding_amount'] = updatedOutstandingAmount; // ✅ 상태 값 변경
      });

      // ✅ 서버 업데이트
      final response = await ApiService.updateClientOutstanding(
        widget.token,
        widget.client['id'],
        {"outstanding_amount": updatedOutstandingAmount},
      );
      for (var item in _scannedItems) {
        final int totalUnits = item['box_quantity'] * item['box_count'];
        final double returnAmount = 0.0; // ✅ 기본적으로 반품 금액 0으로 설정
        final payload = {
          "employee_id": auth.user?.id, // ✅ 직원 ID 포함
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
      // ✅ 반품 상품 서버 전송
      for (var item in _returnedItems) {
        final int totalUnits = item['box_quantity'] * item['box_count'];


        final payload = {
          "employee_id": auth.user?.id,
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": -totalUnits, // ✅ 반품은 음수로 처리
          "sale_datetime": nowStr,
          "return_amount": totalReturnedItemsPrice, // ✅ 반품 금액 추가
        };
        print("📡 반품 데이터 전송: $payload");  // ✅ API 요청 전에 확인
        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("반품 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }


      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("입금이 성공적으로 처리되었습니다.")),
        );

        setState(() {
          _scannedItems = List.from([]); // ✅ 스캔한 상품 목록 초기화
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
          // ✅ 고정된 헤더 (배경색 추가)
          Container(
            height: 35,
            color: Colors.black45,
            child: _buildHeaderRow(),
          ),

          // ✅ 상품 목록 (판매 + 반품)
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.vertical,
              child: Column(
                children: [
                  _buildDataRows(),  // ✅ 판매 상품 리스트
                  _buildReturnRows(), // ✅ 반품 상품 리스트 (같은 구조)
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildReturnRows() {
    return Column(
      children: List.generate(_returnedItems.length, (index) {
        var item = _returnedItems[index];

        // ✅ 반품 합계 금액 정상 계산 (4열 포함)
        double totalPrice = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price']).toDouble() * -0.01;


        return Container(
          decoration: BoxDecoration(
            color: Colors.red.shade50, // ✅ 반품 상품 배경색 (연한 빨간색)
            border: Border(bottom: BorderSide(color: Colors.red.shade300, width: 0.5)), // ✅ 반품 테이블 구분선
          ),
          padding: EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildDataCell(item['name'].toString(), isRed: true),

              _buildDataCell(item['box_count'].toString(), isRed: true), // ✅ 개수 (1씩 증가)
              _buildDataCell("0", isRed: true), // ✅ 박스수 1 고정
              _buildDataCell(item['default_price'].toStringAsFixed(2), isRed: true), // ✅ 원래 상품 가격
              _buildDataCell(item['client_price'].toStringAsFixed(2), isRed: true), // ✅ 이 거래처의 적용 단가
              _buildDataCell(item['price_type'], isRed: true), // ✅ 가격 유형
              _buildDataCell(totalPrice.toStringAsFixed(2), isBold: true, isRed: true),
            ],
          ),
        );
      }),
    );
  }



  Widget _buildHeaderRow() {
    return Row(
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
    );
  }


  List<DataColumn> _buildColumns() {
    return [
      DataColumn(label: _buildHeaderCell('상품명')),
      DataColumn(label: _buildHeaderCell('개수')),
      DataColumn(label: _buildHeaderCell('박스수')),
      DataColumn(label: _buildHeaderCell('가격')),
      DataColumn(label: _buildHeaderCell('단가')),
      DataColumn(label: _buildHeaderCell('유형')),
      DataColumn(
        label: SizedBox(
          width: 120, // ✅ 합계 열을 더 크게 설정
          child: _buildHeaderCell('합계'),
        ),
      ),
    ];
  }

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
            color: Colors.white, // ✅ 헤더 텍스트 색상
          ),
        ),
      ),
    );
  }
  // 상품 목록 테이블을 렌더링
  Widget _buildDataRows() {
    return Column(
      children: List.generate(_scannedItems.length, (index) {
        var item = _scannedItems[index];

        // ✅ 상품 자체의 가격 유형 확인 (is_fixed_price 사용)
        bool isFixedPrice = item['price_type'] == "고정가";


        // ✅ 총 가격 = (박스수량 * 개수 * 단가)
        int totalPrice = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price']* 0.01).round();

        return GestureDetector(
          onTap: () => _selectItem(index), // 클릭 시 해당 상품 선택
          child: Container(
            decoration: BoxDecoration(
              color: index == selectedIndex ? Colors.blue.shade100 : (index.isEven ? Colors.grey.shade100 : Colors.white), // 선택된 행 색상 변경
              border: Border(
                bottom: BorderSide(color: Colors.grey.shade300, width: 0.5), // 가로줄 스타일
              ),
            ),
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildDataCell(item['name'].toString()), // 상품명
                _buildDataCell(item['box_quantity'].toString()), // 박스 수량
                _buildDataCell(item['box_count'].toString()), // 수량
                _buildDataCell(formatter.format(item['default_price'].round())), // ✅ 상품 원래 가격
                _buildDataCell(item['client_price'].toStringAsFixed(2)), // ✅ 거래처 단가
                _buildDataCell(isFixedPrice ? '고정가' : '일반가'), // ✅ 가격 유형
                _buildDataCell(formatter.format(totalPrice), isBold: true), // ✅ 합계
              ],
            ),
          ),
        );
      }),
    );
  }






  DataRow _buildEmptyDataRow() {
    return DataRow(
      cells: List.generate(
        7,
            (index) => DataCell(
          Center(
            child: Text(
              "-",
              style: TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDataCell(String text, {bool isBold = false, bool isRed = false}) {
    return Expanded(
      child: Center(
        child: Text(
          text,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal, // ✅ 합계는 볼드 처리
            color: isRed ? Colors.red : Colors.black87,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }


  Widget _buildSummaryRow() {
    final formatter = NumberFormat("#,###"); // ✅ 천단위 콤마 적용

    // ✅ 판매 상품의 총 박스수량 계산
    int totalBoxCount = _scannedItems.fold(0, (sum, item) {
      int boxQty = (item['box_quantity'] ?? 0).toInt();
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum + (boxQty * boxCnt);
    });

    // ✅ 반품 상품의 총 박스수량 계산 (음수로 적용)
    int totalReturnBoxCount = _returnedItems.fold(0, (sum, item) {
      int boxQty = (item['box_quantity'] ?? 0).toInt();
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum - (boxQty * boxCnt);
    });

    // ✅ 판매 상품의 총 수량 계산
    int totalItemCount = _scannedItems.fold(0, (sum, item) {
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum + boxCnt;
    });

    // ✅ 반품 상품의 총 수량 계산 (음수로 적용)
    int totalReturnItemCount = _returnedItems.fold(0, (sum, item) {
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum - boxCnt;
    });

    // ✅ 판매 상품의 총 판매 금액 계산 (상품 가격 * 거래처 단가 포함)
    int totalSalesAmount = _scannedItems.fold(0, (sum, item) {
      int boxQuantity = (item['box_quantity'] ?? 0);
      int boxCount = (item['box_count'] ?? 0);
      double defaultPrice = item['default_price'] ?? 0.0;
      double clientPrice = item['client_price'] ?? 0.0;

      return sum + ((boxQuantity * boxCount * defaultPrice * clientPrice) * 0.01).round();
    });

    // ✅ 반품 상품의 총 반품 금액 계산 (상품 가격 * 거래처 단가 포함, 음수 적용)
    int totalReturnAmount = _returnedItems.fold(0, (sum, item) {
      int boxQuantity = (item['box_quantity'] ?? 0);
      int boxCount = (item['box_count'] ?? 0);
      double defaultPrice = item['default_price'] ?? 0.0;
      double clientPrice = item['client_price'] ?? 0.0;

      return sum - ((boxQuantity * boxCount * defaultPrice * clientPrice) * 0.01).round();
    });
    totalReturnedItemsPrice = -totalReturnAmount.toDouble();
    // ✅ 최종 총 매출 금액 계산 (판매 - 반품)
    int finalTotal = totalSalesAmount + totalReturnAmount;
    totalScannedItemsPrice = finalTotal.toDouble();
    return Container(
      color: Colors.grey.shade300, // ✅ 배경색 추가 (고정 행 강조)
      padding: EdgeInsets.symmetric(vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryCell("수량 합계", formatter.format(totalBoxCount + totalReturnBoxCount)), // ✅ 천단위 콤마 적용
          _buildSummaryCell("박스수 합계", formatter.format(totalItemCount )), // ✅ 천단위 콤마 적용
          _buildSummaryCell("총 금액", formatter.format(finalTotal) + " 원", isBold: true), // ✅ 천단위 콤마 적용 & 소수점 제거
        ],
      ),
    );
  }



  // ✅ 바코드로 상품 찾기 함수 추가
  Map<String, dynamic>? _findProductByBarcode(String barcode) {
    return _scannedItems.firstWhere(
          (product) => product['barcode'] == barcode,
      orElse: () => <String, dynamic>{}, // ✅ 빈 맵 반환하여 null 방지
    );
  }




// ✅ 합계 행 스타일을 적용하는 함수
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

  //거래처 정보 갱신
  void _fetchUpdatedClientInfo() async {
    try {
      final response = await ApiService.fetchClientById(widget.token, client['id']);
      if (response.statusCode == 200) {
        var updatedClient = jsonDecode(response.body) as Map<String, dynamic>;

        setState(() {
          client = updatedClient; // ✅ 새로운 Map으로 복사하여 UI 강제 갱신
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
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("수량 수정"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // 수량 감소 버튼
                  IconButton(
                    icon: Icon(Icons.remove),
                    onPressed: () {
                      int currentQty = int.tryParse(quantityController.text) ?? 0;
                      if (currentQty > 0) {
                        setState(() {
                          quantityController.text = (currentQty - 1).toString();
                        });
                      }
                    },
                  ),
                  // 수량 입력 필드
                  Expanded(
                    child: TextField(
                      controller: quantityController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(labelText: "수량"),
                    ),
                  ),
                  // 수량 증가 버튼
                  IconButton(
                    icon: Icon(Icons.add),
                    onPressed: () {
                      int currentQty = int.tryParse(quantityController.text) ?? 0;
                      setState(() {
                        quantityController.text = (currentQty + 1).toString();
                      });
                    },
                  ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                int newQuantity = int.tryParse(quantityController.text) ?? 0;
                if (newQuantity > 0) {
                  setState(() {
                    _scannedItems[index]['box_count'] = newQuantity;
                  });
                }
                Navigator.of(context).pop();
              },
              child: Text("수정"),
            ),
          ],
        );
      },
    );
  }
  // 스캔한 상품 삭제
  void _deleteItem(int index) {
    setState(() {
      _scannedItems.removeAt(index); // 해당 인덱스의 상품 삭제
    });
  }

  void _clearAllItems() {
    setState(() {
      _scannedItems.clear(); // 모든 상품 목록 초기화
      _returnedItems.clear(); // ✅ 모든 반품 목록 초기화
    });
    Fluttertoast.showToast(msg: "판매 및 반품 목록이 초기화되었습니다.", gravity: ToastGravity.BOTTOM);
  }


}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'barcode_scanner_page.dart';
import '../product_provider.dart';

class ProductScreen extends StatefulWidget {
  final String token;
  const ProductScreen({super.key, required this.token});

  @override
  State<ProductScreen> createState() => _ProductScreenState();
}

class _ProductScreenState extends State<ProductScreen> {
  String _searchQuery = "";
  late TextEditingController _searchController;
  List<Map<String, dynamic>> _filteredProducts = [];
  final formatter = NumberFormat("#,###");

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _filterProducts() {
    final productProvider = context.read<ProductProvider>();

    setState(() {
      _filteredProducts = productProvider.products
          .where((product) {
        final query = _searchQuery.toLowerCase();
        return (product['product_name']?.toLowerCase().contains(query) ?? false) ||
            (product['brand_id']?.toString().contains(query) ?? false) ||
            (product['default_price']?.toString().contains(query) ?? false) ||
            (product['category']?.toLowerCase().contains(query) ?? false) ||
            (product['barcode']?.contains(query) ?? false);
      })
          .map((product) => Map<String, dynamic>.from(product))
          .toList();
    });
  }

  Future<void> _scanBarcode() async {
    final barcode = await Navigator.push(
      context,
      MaterialPageRoute(builder: (ctx) => const BarcodeScannerPage()),
    );

    if (barcode == null || barcode.isEmpty) return;

    setState(() {
      _searchQuery = barcode;
      _searchController.text = barcode;
      _filterProducts();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("상품 조회"),
        actions: [
          IconButton(
            icon: const Icon(Icons.camera_alt),
            onPressed: _scanBarcode,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: "검색 (상품명, 브랜드, 가격, 바코드 등)",
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: (value) {
                setState(() {
                  _searchQuery = value;
                  _filterProducts();
                });
              },
            ),
          ),

          Expanded(
            child: _buildProductTable(),
          ),
        ],
      ),
    );
  }

  Widget _buildProductTable() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal, // ✅ 가로 스크롤 추가
      child: Column(
        children: [
          // ✅ 고정된 헤더
          Container(
            height: 35,
            color: Colors.black45,
            child: _buildHeaderRow(),
          ),

          // ✅ 검색된 상품 목록
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.vertical,
              child: Column(
                children: _filteredProducts.isNotEmpty
                    ? _buildDataRows()
                    : [_buildEmptyRow()], // 검색 결과 없을 경우 빈 줄 추가
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderRow() {
    return Row(
      children: [
        _buildHeaderCell("상품명", width: 150),
        _buildHeaderCell("브랜드", width: 100),
        _buildHeaderCell("가격", width: 100),
        _buildHeaderCell("바코드", width: 200), // ✅ 바코드 칸 넓게 조정
        _buildHeaderCell("카테고리", width: 100),
        _buildHeaderCell("가격 유형", width: 100),
      ],
    );
  }

  Widget _buildHeaderCell(String text, {double width = 100}) {
    return SizedBox(
      width: width,
      child: Container(
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  List<Widget> _buildDataRows() {
    return List.generate(_filteredProducts.length, (index) {
      var product = _filteredProducts[index];
      bool isFixedPrice = product['is_fixed_price'] == true; // ✅ 가격 유형 확인

      return Container(
        decoration: BoxDecoration(
          color: index.isEven ? Colors.grey.shade100 : Colors.white,
          border: Border(bottom: BorderSide(color: Colors.grey.shade300, width: 0.5)),
        ),
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          children: [
            _buildDataCell(product['product_name'].toString(), width: 150),
            _buildDataCell(product['brand_id'].toString(), width: 100),
            _buildDataCell(formatter.format((product['default_price'] as num).toInt()), width: 100),
            _buildDataCellWithPopup(product['barcode'] ?? "-", width: 200), // ✅ 바코드 칸 넓게 조정
            _buildDataCell(product['category'] ?? "-", width: 100),
            _buildDataCell(isFixedPrice ? "고정가" : "일반가", width: 100, isBold: true),
          ],
        ),
      );
    });
  }

  Widget _buildEmptyRow() {
    return Container(
      padding: const EdgeInsets.all(16.0),
      child: const Text(
        "검색 결과가 없습니다.",
        style: TextStyle(fontSize: 16, color: Colors.grey),
      ),
    );
  }

  Widget _buildDataCell(String text, {double width = 100, bool isBold = false}) {
    return SizedBox(
      width: width,
      child: Center(
        child: Text(
          text,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: Colors.black87,
          ),
          textAlign: TextAlign.center,
          overflow: TextOverflow.ellipsis, // ✅ 글자가 넘칠 경우 "..." 처리
        ),
      ),
    );
  }
  void _showPopup(String fullText) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text("상세 정보"),
          content: Text(fullText),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("닫기"),
            ),
          ],
        );
      },
    );
  }

  Widget _buildDataCellWithPopup(String text, {double width = 100}) {
    bool isOverflowing = text.length > 10; // ✅ 10자 이상이면 팝업 표시

    return SizedBox(
      width: width,
      child: GestureDetector(
        onTap: isOverflowing ? () => _showPopup(text) : null,
        child: Center(
          child: Text(
            isOverflowing ? "${text.substring(0, 10)}..." : text,
            style: const TextStyle(fontSize: 12, color: Colors.black87),
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}

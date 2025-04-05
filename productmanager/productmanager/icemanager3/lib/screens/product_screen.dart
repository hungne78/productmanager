import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'barcode_scanner_page.dart';
import '../product_provider.dart';
import '../screens/home_screen.dart';
import '../auth_provider.dart';

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
    // ✅ 최초 진입 시 상품 목록을 바로 보여줌
    _searchController = TextEditingController(); // ✅ 반드시 초기화!
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final productProvider = context.read<ProductProvider>();
      setState(() {
        _filteredProducts = List<Map<String, dynamic>>.from(productProvider.products);
      });
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
  void _loadAllProducts() {
    final productProvider = context.read<ProductProvider>();
    setState(() {
      _filteredProducts = List<Map<String, dynamic>>.from(productProvider.products);
    });
  }

  void _filterProducts() {
    final productProvider = context.read<ProductProvider>();

    setState(() {
      _filteredProducts = productProvider.products
          .where((product) {
        final query = _searchQuery.toLowerCase();
        return (product['product_name']?.toLowerCase().contains(query) ?? false) ||
            (product['brand_name']?.toString().contains(query) ?? false) ||
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
  void _showPopup(Map<String, dynamic> product) {
    final formatter = NumberFormat("#,###");
    final bool isFixedPrice = product['is_fixed_price'] == true;

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(product['product_name'] ?? "상품 상세 정보"),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                _popupLine("상품명", product['product_name']),
                _popupLine("브랜드", product['brand_name']),
                _popupLine("가격", "${formatter.format(product['default_price'])} 원"),
                _popupLine("가격 유형", isFixedPrice ? "고정가" : "일반가"),
                _popupLine("바코드", (product['barcodes'] as List<dynamic>?)?.join('\n') ?? "-"),

                _popupLine("카테고리", product['category']),
                _popupLine("박스당 수량", product['box_quantity']),
                _popupLine("창고 재고", product['stock']),
                const SizedBox(height: 8),
                if (product.containsKey("description"))
                  Text("📌 설명: ${product['description']}", style: TextStyle(color: Colors.black87)),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("닫기"),
            ),
          ],
        );
      },
    );
  }
  Widget _popupLine(String label, dynamic value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: RichText(
        text: TextSpan(
          style: const TextStyle(fontSize: 14, color: Colors.black),
          children: [
            TextSpan(text: "$label: ", style: const TextStyle(fontWeight: FontWeight.bold)),
            TextSpan(text: "${value ?? '-'}"),
          ],
        ),
      ),
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(56),
        child: AppBar(
          backgroundColor: Colors.indigo,
          elevation: 3,
          centerTitle: true,
          leading: IconButton(
            icon: const Icon(Icons.home, color: Colors.white),
            onPressed: () {
              final token = context.read<AuthProvider>().user?.token;
              if (token != null) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => HomeScreen(token: token)),
                );
              }
            },
          ),
          title: const Text(
            "상품 조회",
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 18,
              color: Colors.white,
            ),
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.camera_alt, color: Colors.white), // ✅ 흰색 아이콘
              onPressed: _scanBarcode,
            ),
          ],
        ),
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
                _searchQuery = value;
                if (_searchQuery.isEmpty) {
                  _loadAllProducts();
                } else {
                  _filterProducts();
                }
              },
            ),
          ),
          _buildHeader(),
          const Divider(height: 1),
          Expanded(child: _buildProductList()),
        ],
      ),
    );
  }


  Widget _buildHeader() {
    return Container(
      color: Colors.indigo.shade600,
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: const [
          _TableHeader("상품명", flex: 3),
          _TableHeader("브랜드", flex: 2),
          _TableHeader("가격", flex: 2),
          _TableHeader("바코드", flex: 3),
          _TableHeader("카테고리", flex: 2),
          _TableHeader("유형", flex: 2),
        ],
      ),
    );
  }
  Widget _buildProductList() {
    if (_filteredProducts.isEmpty) {
      return const Center(child: Text("검색 결과가 없습니다."));
    }

    return ListView.separated(
      itemCount: _filteredProducts.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (context, index) {
        final product = _filteredProducts[index];
        final isFixedPrice = product['is_fixed_price'] == true;

        return GestureDetector(
          onTap: () => _showPopup(product),
          child: Container(
            color: index.isEven ? Colors.grey.shade100 : Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: Row(
              children: [
                _TableCell(product['product_name'] ?? "-", flex: 3),
                _TableCell(product['brand_name']?.toString() ?? "-", flex: 2),
                _TableCell(formatter.format((product['default_price'] ?? 0).toInt()), flex: 2),
                _TableCell(
                    (product['barcodes'] != null && product['barcodes'].isNotEmpty)
                        ? product['barcodes'][0]
                        : "-",
                    flex: 3
                ),
                _TableCell(product['category'] ?? "-", flex: 2),
                _TableCell(isFixedPrice ? "고정가" : "일반가", flex: 2, isBold: true),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _TableHeader extends StatelessWidget {
  final String label;
  final int flex;

  const _TableHeader(this.label, {required this.flex});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      flex: flex,
      child: Center(
        child: Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ),
    );
  }
}

class _TableCell extends StatelessWidget {
  final String text;
  final int flex;
  final bool isBold;

  const _TableCell(this.text, {required this.flex, this.isBold = false});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      flex: flex,
      child: Center(
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
          ),
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }


  Widget _buildDataCell(String text, {int flex = 1, bool isBold = false}) {
    return Expanded(
      flex: flex,
      child: Center(
        child: Text(
          text,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: Colors.black87,
          ),
          textAlign: TextAlign.center,
          overflow: TextOverflow.ellipsis,
        ),
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


}

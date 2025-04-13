// lib/screens/purchases/purchase_list_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../providers/auth_provider.dart';
import '../../services/purchase_api_service.dart';
import 'purchase_detail_screen.dart';

class PurchaseListScreen extends StatefulWidget {
  const PurchaseListScreen({Key? key}) : super(key: key);

  @override
  _PurchaseListScreenState createState() => _PurchaseListScreenState();
}

class _PurchaseListScreenState extends State<PurchaseListScreen> {
  // 필터
  DateTime _startDate = DateTime.now().subtract(const Duration(days: 30));
  DateTime _endDate = DateTime.now();
  int? _selectedSupplierId;
  int? _selectedProductId;

  bool _isLoading = false;
  String? _error;
  List<Map<String, dynamic>> _purchaseList = [];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("매입(입고) 정보"),
      ),
      body: Column(
        children: [
          // (A) 필터 바
          _buildFilterBar(),

          // (B) 검색 버튼
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: ElevatedButton.icon(
              icon: const Icon(Icons.search),
              label: const Text("검색"),
              onPressed: _search,
            ),
          ),

          // (C) 결과 리스트
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : _buildPurchaseListView(),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterBar() {
    final fmt = DateFormat("yyyy-MM-dd");
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Row(
        children: [
          // 날짜 범위
          TextButton.icon(
            icon: const Icon(Icons.calendar_month),
            label: Text(fmt.format(_startDate)),
            onPressed: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: _startDate,
                firstDate: DateTime(2022),
                lastDate: DateTime(2030),
              );
              if (picked != null) {
                setState(() => _startDate = picked);
              }
            },
          ),
          const SizedBox(width: 10),
          TextButton.icon(
            icon: const Icon(Icons.calendar_month),
            label: Text(fmt.format(_endDate)),
            onPressed: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: _endDate,
                firstDate: DateTime(2022),
                lastDate: DateTime(2030),
              );
              if (picked != null) {
                setState(() => _endDate = picked);
              }
            },
          ),
          const SizedBox(width: 12),

          // 공급사 ID
          Row(
            children: [
              const Text("공급사ID: "),
              SizedBox(
                width: 70,
                child: TextField(
                  keyboardType: TextInputType.number,
                  onChanged: (val) => _selectedSupplierId = int.tryParse(val),
                  decoration: const InputDecoration(hintText: "전체"),
                ),
              )
            ],
          ),
          const SizedBox(width: 12),

          // 상품 ID
          Row(
            children: [
              const Text("상품ID: "),
              SizedBox(
                width: 70,
                child: TextField(
                  keyboardType: TextInputType.number,
                  onChanged: (val) => _selectedProductId = int.tryParse(val),
                  decoration: const InputDecoration(hintText: "전체"),
                ),
              )
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPurchaseListView() {
    if (_purchaseList.isEmpty) {
      return const Center(child: Text("조회 결과가 없습니다."));
    }
    return ListView.builder(
      itemCount: _purchaseList.length,
      itemBuilder: (ctx, i) {
        final item = _purchaseList[i];
        final purchaseId = item["purchase_id"];
        final date = item["purchase_date"] ?? "N/A";
        final supplierName = item["supplier_name"] ?? "공급사 없음";
        final totalAmount = item["total_amount"] ?? 0;

        return Card(
          margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          child: ListTile(
            leading: CircleAvatar(child: Text("$purchaseId")),
            title: Text("$supplierName / $date"),
            subtitle: Text("합계: $totalAmount 원"),
            onTap: () {
              // 상세 화면 이동
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => PurchaseDetailScreen(purchaseId: purchaseId),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Future<void> _search() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _purchaseList = [];
    });

    final token = context.read<AuthProvider>().token;
    if (token == null) {
      setState(() {
        _isLoading = false;
        _error = "로그인이 필요합니다.";
      });
      return;
    }

    try {
      final data = await PurchaseApiService.fetchPurchaseList(
        token,
        startDate: _startDate,
        endDate: _endDate,
        supplierId: _selectedSupplierId,
        productId: _selectedProductId,
      );
      // data: [
      //   { "purchase_id":1,"purchase_date":"2025-05-10","supplier_name":"XXX상사", "total_amount":30000, ...},
      //   ...
      // ]
      setState(() => _purchaseList = data);
    } catch (e) {
      setState(() => _error = "검색 실패: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }
}

// lib/screens/purchases/purchase_detail_screen.dart

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../services/purchase_api_service.dart';

class PurchaseDetailScreen extends StatefulWidget {
  final int purchaseId;
  const PurchaseDetailScreen({Key? key, required this.purchaseId}) : super(key: key);

  @override
  _PurchaseDetailScreenState createState() => _PurchaseDetailScreenState();
}

class _PurchaseDetailScreenState extends State<PurchaseDetailScreen> {
  bool _isLoading = false;
  Map<String, dynamic>? _purchase; // { purchase_id, purchase_date, supplier, items:[], ... }
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchDetail();
  }

  Future<void> _fetchDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _purchase = null;
    });

    try {
      final data = await PurchaseApiService.fetchPurchaseDetail(widget.purchaseId);
      setState(() => _purchase = data);
    } catch (e) {
      setState(() => _error = "상세 조회 실패: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = NumberFormat("#,###");
    return Scaffold(
      appBar: AppBar(
        title: Text("매입 상세 #${widget.purchaseId}"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
          : _purchase == null
          ? const Center(child: Text("입고 정보를 불러올 수 없습니다."))
          : _buildDetailView(f),
    );
  }

  Widget _buildDetailView(NumberFormat f) {
    final purchaseId = _purchase!["purchase_id"];
    final purchaseDate = _purchase!["purchase_date"] ?? "N/A";
    final supplierName = _purchase!["supplier_name"] ?? "공급사 없음";
    final totalAmount = _purchase!["total_amount"] ?? 0;
    final items = List<Map<String, dynamic>>.from(_purchase!["items"] ?? []);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("입고 ID: $purchaseId", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text("입고 날짜: $purchaseDate"),
          Text("공급사: $supplierName"),
          const Divider(height: 20, thickness: 1),
          Text("📦 상품 목록", style: const TextStyle(fontWeight: FontWeight.bold)),

          ...items.map((e) {
            final productName = e["product_name"] ?? "이름 없음";
            final quantity = e["quantity"] ?? 0;
            final unitPrice = e["unit_price"] ?? 0;
            final lineTotal = quantity * unitPrice;
            return ListTile(
              contentPadding: const EdgeInsets.symmetric(vertical: 4),
              title: Text(productName),
              subtitle: Text(
                "수량: $quantity, 단가: ${f.format(unitPrice)} 원\n"
                    "합계: ${f.format(lineTotal)} 원",
              ),
            );
          }).toList(),

          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: Text("총 합계: ${f.format(totalAmount)} 원",
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),

          // 만약 "재고 반영" 기능이 있다면 여기서 버튼 추가
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _handleApplyStock,
            icon: const Icon(Icons.playlist_add_check),
            label: const Text("창고 재고 반영"),
          ),
        ],
      ),
    );
  }

  void _handleApplyStock() async {
    // 이 예시는 단순 버튼 클릭 시 '창고 재고/직원 재고'에 반영하는 로직.
    // 실제로는 API를 호출하거나, 각 상품별로 얼만큼을 어느 직원 차량에 배분할지 등 여러 단계가 필요할 수도 있음.
    // 여기서는 단순히 알림만 표시하는 예시
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("재고 반영 로직 실행!")),
    );
  }
}

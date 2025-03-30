import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/product_provider.dart';
import '../services/api_service.dart';

class FranchiseOrderScreen extends StatelessWidget {
  final DateTime selectedDate;
  final int shipmentRound;

  const FranchiseOrderScreen({
    super.key,
    required this.selectedDate,
    required this.shipmentRound,
  });

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final productProvider = Provider.of<ProductProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text("주문 작성"),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            _buildHeader(auth),
            const SizedBox(height: 12),
            Expanded(child: _buildProductList(productProvider)),
            const SizedBox(height: 12),
            _buildSummary(context, auth, productProvider),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(AuthProvider auth) {
    final now = DateTime.now();
    final dateStr = "${now.year}-${now.month}-${now.day}";

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("📅 날짜: $dateStr"),
        const SizedBox(height: 4),
        Text("🏪 거래처: ${auth.clientName ?? '알 수 없음'}"),
      ],
    );
  }

  Widget _buildProductList(ProductProvider productProvider) {
    final products = productProvider.products;

    return ListView.separated(
      itemCount: products.length,
      separatorBuilder: (_, __) => const Divider(),
      itemBuilder: (context, index) {
        final p = products[index];
        final qty = productProvider.getQuantity(p['id']);

        return ListTile(
          title: Text(p['product_name']),
          subtitle: Text("브랜드: ${p['brand_name']} / 카테고리: ${p['category_name']} / 박스: ${p['box_quantity']}개"),
          trailing: SizedBox(
            width: 100,
            child: TextField(
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(hintText: "수량"),
              controller: TextEditingController(text: qty.toString()),
              onChanged: (val) {
                final q = int.tryParse(val) ?? 0;
                productProvider.setQuantity(p['id'], q);
              },
            ),
          ),
        );
      },
    );
  }

  Widget _buildSummary(BuildContext context, AuthProvider auth, ProductProvider productProvider) {
    final totalQty = productProvider.totalQuantity;
    final totalPrice = productProvider.getTotalAmount();
    final outstanding = 100000; // 👉 서버에서 받아온 미수금으로 대체 필요

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("💰 미수금: ${outstanding.toStringAsFixed(0)} 원"),
        Text("📦 총 수량: $totalQty 박스"),
        Text("💵 총 금액: ${totalPrice.toStringAsFixed(0)} 원"),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: () async {
            final result = await _submitOrder(context, auth, productProvider);
            if (result) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("주문이 전송되었습니다.")),
              );
              Navigator.pop(context);
            }
          },
          child: const Text("주문 전송"),
        )
      ],
    );
  }

  Future<bool> _submitOrder(BuildContext context, AuthProvider auth, ProductProvider productProvider) async {
    final filteredItems = productProvider.quantities.entries
        .where((e) => e.value > 0)
        .map((e) => {
      "product_id": e.key,
      "quantity": e.value,
    })
        .toList();

    if (filteredItems.isEmpty) return false;

    try {
      await ApiService.submitFranchiseOrder(
        clientId: auth.clientId!,
        orderDate: DateTime.now(), // or 서버 시간
        shipmentRound: 0, // 출고차수: 날짜 선택 화면에서 받아오기
        items: filteredItems,
      );
      return true;
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("주문 실패: $e")),
      );
      return false;
    }
  }
}

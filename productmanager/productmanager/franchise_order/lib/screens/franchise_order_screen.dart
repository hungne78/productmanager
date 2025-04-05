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
    final productProvider = context.watch<ProductProvider>();
    final auth = context.watch<AuthProvider>();
    final grouped = productProvider.groupedByCategoryBrand;

    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(70),
        child: AppBar(
          automaticallyImplyLeading: false,
          elevation: 4,
          centerTitle: true,
          backgroundColor: Colors.indigo,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
          ),
          title: Row(
            mainAxisSize: MainAxisSize.min,
            children: const [
              Icon(Icons.shopping_cart, color: Colors.white, size: 26),
              SizedBox(width: 8),
              Text(
                "가맹점 주문",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildHeader(auth),
                const SizedBox(height: 12),
                ...grouped.entries.map((categoryEntry) {
                  final category = categoryEntry.key;
                  final brandMap = categoryEntry.value;

                  return ExpansionTile(
                    title: Text("📦 $category"),
                    initiallyExpanded: false,
                    maintainState: true,
                    childrenPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    children: brandMap.entries.expand((brandEntry) {
                      final brand = brandEntry.key;
                      final products = brandEntry.value;

                      return [
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          child: Text(
                            "🏷️ $brand",
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.grey,
                            ),
                          ),
                        ),
                        ...products.map((product) {
                          final name = product['product_name'] ?? '이름 없음';
                          final price = product['default_price'] ?? 0;
                          final qty = productProvider.getQuantity(product['id']);
                          final controller = TextEditingController(text: qty.toString());

                          return Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            child: Column(
                              children: [
                                const Divider(thickness: 1),
                                ListTile(
                                  tileColor: Colors.white,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                  title: Text(name),
                                  subtitle: Text("₩$price"),
                                  trailing: SizedBox(
                                    width: 70,
                                    child: TextFormField(
                                      controller: controller,
                                      keyboardType: TextInputType.number,
                                      decoration: InputDecoration(
                                        hintText: "수량",
                                        contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                                        filled: true,
                                        fillColor: Colors.grey[100],
                                      ),
                                      onTap: () {
                                        controller.selection = TextSelection(
                                          baseOffset: 0,
                                          extentOffset: controller.text.length,
                                        );
                                      },
                                      onChanged: (val) {
                                        final q = int.tryParse(val) ?? 0;
                                        productProvider.setQuantity(product['id'], q);
                                      },
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                      ];
                    }).toList(),
                  );
                }).toList(),
                const SizedBox(height: 24),
              ],
            ),
          ),

          // ✅ 고정된 합계 영역
          Container(
            decoration: BoxDecoration(
              color: Colors.indigo[50],
              border: const Border(top: BorderSide(color: Colors.grey)),
            ),
            padding: const EdgeInsets.all(16),
            child: _buildSummary(context, auth, productProvider),
          ),
        ],
      ),
    );
  }


  Widget _buildHeader(AuthProvider auth) {
    final dateStr = "${selectedDate.year}-${selectedDate.month.toString().padLeft(2, '0')}-${selectedDate.day.toString().padLeft(2, '0')}";

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("📅 주문 날짜: $dateStr", style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 6),
            Text("🏪 거래처명: ${auth.clientName ?? '알 수 없음'}", style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 6),
            Text("🚚 출고차수: ${shipmentRound}차", style: const TextStyle(fontSize: 16)),
          ],
        ),
      ),
    );
  }

  Widget _buildSummary(BuildContext context, AuthProvider auth, ProductProvider productProvider) {
    final totalQty = productProvider.totalQuantity;
    final totalPrice = productProvider.getTotalAmount();
    final outstanding = 100000; // 👉 서버에서 받아온 미수금으로 대체 가능

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("💰 미수금: ${outstanding.toStringAsFixed(0)} 원"),
        Text("📦 총 수량: $totalQty 박스"),
        Text("💵 총 금액: ${totalPrice.toStringAsFixed(0)} 원"),
        const SizedBox(height: 12),
        Center(
          child: ElevatedButton.icon(
            onPressed: () async {
              final result = await _submitOrder(context, auth, productProvider);
              if (result) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("✅ 주문이 전송되었습니다.")),
                );
                Navigator.pop(context);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.indigo,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            icon: const Icon(Icons.send, color: Colors.white),
            label: const Text("주문 전송", style: TextStyle(color: Colors.white)),
          ),
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

    if (filteredItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("주문할 상품을 1개 이상 입력해주세요.")),
      );
      return false;
    }

    try {
      await ApiService.submitFranchiseOrder(
        clientId: auth.clientId!,
        orderDate: selectedDate,
        shipmentRound: shipmentRound,
        items: filteredItems,
      );
      return true;
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("❌ 주문 실패: $e")),
      );
      return false;
    }
  }
}

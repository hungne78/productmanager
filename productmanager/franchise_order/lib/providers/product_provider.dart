import 'package:flutter/material.dart';
import 'dart:collection';

class ProductProvider extends ChangeNotifier {
  // ✅ 카테고리별 상품 그룹
  LinkedHashMap<String, List<Map<String, dynamic>>> _groupedProducts = LinkedHashMap();

  // ✅ 전체 상품 리스트 (flat)
  List<Map<String, dynamic>> _products = [];

  // ✅ 수량 저장: productId → 수량
  Map<int, int> _quantities = {};

  // ✅ getters
  LinkedHashMap<String, List<Map<String, dynamic>>> get groupedProducts => _groupedProducts;
  List<Map<String, dynamic>> get products => _products;
  Map<int, int> get quantities => _quantities;

  // ✅ 기존 방식 (단순 리스트 등록)
  void setProducts(List<Map<String, dynamic>> productList) {
    _products = productList;
    _groupedProducts = LinkedHashMap.from({
      "전체": productList,
    });
    _initializeQuantities(productList);
  }

  // ✅ 새로운 방식 (카테고리별 Map 등록)
  void setGroupedProducts(Map<String, List<Map<String, dynamic>>> grouped) {
    _groupedProducts = LinkedHashMap.of(grouped);
    _products = grouped.values.expand((e) => e).toList();
    _initializeQuantities(_products);
  }

  // ✅ 수량 초기화
  void _initializeQuantities(List<Map<String, dynamic>> productList) {
    _quantities = {
      for (var p in productList) p['id'] as int: 0
    };
    notifyListeners();
  }

  void setQuantity(int productId, int qty) {
    _quantities[productId] = qty;
    notifyListeners();
  }

  void increment(int productId) {
    _quantities[productId] = (_quantities[productId] ?? 0) + 1;
    notifyListeners();
  }

  void decrement(int productId) {
    if ((_quantities[productId] ?? 0) > 0) {
      _quantities[productId] = _quantities[productId]! - 1;
      notifyListeners();
    }
  }

  int getQuantity(int productId) => _quantities[productId] ?? 0;

  int get totalQuantity => _quantities.values.fold(0, (a, b) => a + b);

  double getTotalAmount() {
    double total = 0;
    for (var p in _products) {
      final id = p['id'] as int;
      final qty = _quantities[id] ?? 0;
      final boxQty = (p['box_quantity'] ?? 1).toDouble();
      final price = (p['fixed_price'] ?? p['default_price'] ?? 0).toDouble();
      total += price * boxQty * qty;
    }
    return total;
  }
  LinkedHashMap<String, LinkedHashMap<String, List<Map<String, dynamic>>>> _groupedByCategoryBrand = LinkedHashMap();

  void setGroupedCategoryBrand(
      LinkedHashMap<String, LinkedHashMap<String, List<Map<String, dynamic>>>> data,
      List<String> categoryOrder,
      List<String> brandOrder,
      ) {
    final sorted = LinkedHashMap<String, LinkedHashMap<String, List<Map<String, dynamic>>>>();

    // 카테고리 정렬
    for (final cat in categoryOrder) {
      if (data.containsKey(cat)) {
        final brandMap = data[cat]!;

        // 브랜드 정렬
        final sortedBrand = LinkedHashMap<String, List<Map<String, dynamic>>>();
        for (final brand in brandOrder) {
          if (brandMap.containsKey(brand)) {
            sortedBrand[brand] = brandMap[brand]!;
          }
        }

        // 기타 브랜드 추가 (정의 안된 순서)
        brandMap.forEach((k, v) {
          if (!sortedBrand.containsKey(k)) {
            sortedBrand[k] = v;
          }
        });

        sorted[cat] = sortedBrand;
      }
    }

    // 기타 카테고리 추가
    data.forEach((k, v) {
      if (!sorted.containsKey(k)) {
        sorted[k] = v;
      }
    });

    _groupedByCategoryBrand = sorted;
    _products = sorted.values.expand((bMap) => bMap.values.expand((list) => list)).toList();
    _initializeQuantities(_products);
    notifyListeners();
  }




  LinkedHashMap<String, LinkedHashMap<String, List<Map<String, dynamic>>>> get groupedByCategoryBrand => _groupedByCategoryBrand;

  final Map<int, TextEditingController> _controllers = {};

  TextEditingController getController(int productId) {
    if (!_controllers.containsKey(productId)) {
      _controllers[productId] = TextEditingController(text: getQuantity(productId).toString());
    }
    return _controllers[productId]!;
  }

}

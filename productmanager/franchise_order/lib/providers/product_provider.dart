import 'package:flutter/material.dart';

class ProductProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _products = [];
  Map<int, int> _quantities = {}; // productId → 수량

  List<Map<String, dynamic>> get products => _products;
  Map<int, int> get quantities => _quantities;

  void setProducts(List<Map<String, dynamic>> productList) {
    _products = productList;
    _quantities = {
      for (var product in productList) product['id'] as int: 0
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
}

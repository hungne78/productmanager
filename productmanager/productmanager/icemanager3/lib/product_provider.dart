import 'package:flutter/material.dart';

class ProductProvider extends ChangeNotifier {
  List<dynamic> _products = [];
  Map<String, dynamic> _groupedProducts = {}; // ✅ 그룹화된 상품용

  List<dynamic> get products => _products;
  Map<String, dynamic> get groupedProducts => _groupedProducts;

  void setProducts(List<dynamic> newProducts) {
    _products = newProducts.where((p) => p != null).toList();
    notifyListeners();
  }

  void setGroupedProducts(Map<String, dynamic> grouped) {
    _groupedProducts = grouped;
    notifyListeners();
  }

  void clearProducts() {
    _products = [];
    _groupedProducts = {};
    notifyListeners();
  }
}

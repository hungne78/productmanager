import 'package:flutter/material.dart';

class ProductProvider extends ChangeNotifier {
  List<dynamic> _products = [];

  List<dynamic> get products => _products;

  void setProducts(List<dynamic> newProducts) {
    _products = newProducts.where((p) => p != null).toList();
    notifyListeners();
  }

  void clearProducts() {
    _products = [];
    notifyListeners();
  }
}

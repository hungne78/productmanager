import 'package:flutter/material.dart';

class VehicleStockProvider extends ChangeNotifier {
  Map<int, int> _vehicleStock = {}; // {상품 ID: 차량 재고 수량}

  Map<int, int> get vehicleStock => _vehicleStock;

  // ✅ 차량 재고 초기화 (앱 실행 시 불러오기)
  void initializeStock(Map<int, int> initialStock) {
    _vehicleStock = initialStock;
    notifyListeners();
  }

  // ✅ 주문 발생 시 재고 추가
  void addStock(int productId, int quantity) {
    _vehicleStock[productId] = (_vehicleStock[productId] ?? 0) + quantity;
    notifyListeners();
  }

  // ✅ 매출 발생 시 재고 차감
  void removeStock(int productId, int quantity) {
    _vehicleStock[productId] = (_vehicleStock[productId] ?? 0) - quantity;
    notifyListeners();
  }

  // ✅ 특정 상품의 재고 확인
  int getStock(int productId) {
    return _vehicleStock[productId] ?? 0;
  }
}

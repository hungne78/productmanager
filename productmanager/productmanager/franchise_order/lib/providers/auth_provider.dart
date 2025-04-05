import 'package:flutter/material.dart';

class AuthProvider extends ChangeNotifier {
  int? _clientId;
  String? _clientName;
  String? _token;

  int? get clientId => _clientId;
  String? get clientName => _clientName;
  String? get token => _token;

  bool get isLoggedIn => _clientId != null;

  void setClientData({
    required int clientId,
    required String clientName,
    String? token,
  }) {
    _clientId = clientId;
    _clientName = clientName;
    _token = token;
    notifyListeners();
  }

  void logout() {
    _clientId = null;
    _clientName = null;
    _token = null;
    notifyListeners();
  }
}

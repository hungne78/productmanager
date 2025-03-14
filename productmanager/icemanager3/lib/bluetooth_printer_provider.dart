import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

class BluetoothPrinterProvider with ChangeNotifier {
  BluetoothDevice? _selectedDevice;
  BluetoothCharacteristic? _writeCharacteristic;
  bool _isConnected = false;
  List<BluetoothDevice> _devicesList = [];
  bool _isScanning = false;

  BluetoothDevice? get selectedDevice => _selectedDevice;
  bool get isConnected => _isConnected;
  List<BluetoothDevice> get devicesList => _devicesList;
  bool get isScanning => _isScanning;

  /// 🔹 블루투스 장치 검색 시작
  void startScan() async {
    if (_isScanning) return;
    _isScanning = true;
    notifyListeners();

    FlutterBluePlus.startScan(timeout: const Duration(seconds: 4));

    Timer(Duration(seconds: 5), () {
      _isScanning = false;
      notifyListeners();
    });

    FlutterBluePlus.scanResults.listen((results) {
      _devicesList = results
          .map((r) => r.device)
          .where((device) => device.name.isNotEmpty)
          .toList();
      notifyListeners();
    });
  }

  /// 🔹 마지막으로 연결한 프린터 정보 로드
  Future<void> loadLastDevice() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? lastDeviceId = prefs.getString('last_printer_id');
    if (lastDeviceId != null) {
      attemptReconnect(lastDeviceId);
    }
  }

  /// 🔹 저장된 프린터 ID로 자동 연결 시도
  Future<void> attemptReconnect(String deviceId) async {
    List<BluetoothDevice> connectedDevices = await FlutterBluePlus.connectedDevices;
    for (var device in connectedDevices) {
      if (device.id.toString() == deviceId) {
        connectToDevice(device);
        return;
      }
    }
  }

  /// 🔹 블루투스 프린터 연결 및 **Provider에 저장**
  Future<void> connectToDevice(BluetoothDevice device) async {
    if (_isConnected) return;

    try {
      await device.connect();
      List<BluetoothService> services = await device.discoverServices();
      for (BluetoothService service in services) {
        for (BluetoothCharacteristic characteristic in service.characteristics) {
          if (characteristic.properties.write) {
            _writeCharacteristic = characteristic;
            break;
          }
        }
      }

      _selectedDevice = device;
      _isConnected = true;
      notifyListeners();

      // ✅ 연결된 프린터 정보 저장
      SharedPreferences prefs = await SharedPreferences.getInstance();
      await prefs.setString('last_printer_id', device.id.toString());
    } catch (e) {
      print("❌ 블루투스 연결 실패: $e");
    }
  }

  /// 🔹 블루투스 프린터 연결 해제
  Future<void> disconnectDevice() async {
    if (_selectedDevice != null) {
      await _selectedDevice!.disconnect();
      _selectedDevice = null;
      _isConnected = false;
      notifyListeners();
    }
  }
}

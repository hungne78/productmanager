import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
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

  Future<BluetoothCharacteristic?> autoDetectPrinter(BluetoothDevice device) async {
    print("🔍 [autoDetectPrinter] BLE 프린터 자동 탐색 시작: ${device.name}");

    // 이미 연결 안 된 상태라면 먼저 연결
    if (device.state != BluetoothDeviceState.connected) {
      await device.connect();
    }

    // 서비스/캐릭터리스틱 검색
    final services = await device.discoverServices();
    BluetoothCharacteristic? foundWriteChar;

    // 모든 Characteristic 중에서 write 가능(프린터 전송용)인지 확인
    for (var s in services) {
      for (var c in s.characteristics) {
        if (c.properties.write) {
          print("✅ 후보 WRITE Characteristic: ${c.uuid}");

          // 간단 테스트: 프린터에 임의 문구 전송
          try {
            await c.write(utf8.encode("Hello Printer\n"));
            print("🎉 프린터 WRITE 성공 → Characteristic: ${c.uuid}");
            foundWriteChar = c;
            break; // 찾았으면 탈출
          } catch (e) {
            print("⚠️ 쓰기 실패: $e");
          }
        }
      }
      if (foundWriteChar != null) break;
    }

    if (foundWriteChar == null) {
      print("❌ 프린터로 쓸 만한 WRITE Characteristic을 찾지 못함");
    }
    return foundWriteChar;
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
      // [수정] 여기서 자동 탐색
      final foundWriteChar = await autoDetectPrinter(device);

      if (foundWriteChar == null) {
        print("❌ writeCharacteristic을 찾지 못해 프린터 연결 실패");
        return;
      }

      _writeCharacteristic = foundWriteChar;
      _selectedDevice = device;
      _isConnected = true;
      notifyListeners();

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

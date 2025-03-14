import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:ui' as ui;
import 'package:image/image.dart' as img;


class BluetoothPrinterScreen extends StatefulWidget {
  @override
  _BluetoothPrinterScreenState createState() => _BluetoothPrinterScreenState();
}

class _BluetoothPrinterScreenState extends State<BluetoothPrinterScreen> {
  List<BluetoothDevice> _devicesList = [];
  BluetoothDevice? _selectedDevice;
  BluetoothCharacteristic? _writeCharacteristic;
  bool _isConnecting = false;
  bool _isConnected = false;
  StreamSubscription? _scanSubscription;
  bool _isScanning = false;

  @override
  void initState() {
    super.initState();
    _loadLastDevice();
    print("📌 BluetoothPrinterScreen 시작됨");
    _startScan();
  }
  /// 🔹 마지막으로 연결한 프린터 정보 로드
  Future<void> _loadLastDevice() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? lastDeviceId = prefs.getString('last_printer_id');
    if (lastDeviceId != null) {
      _attemptReconnect(lastDeviceId);
    }
  }

  /// 🔹 저장된 프린터 ID로 자동 연결 시도
  Future<void> _attemptReconnect(String deviceId) async {
    List<BluetoothDevice> connectedDevices = await FlutterBluePlus.connectedDevices;
    for (var device in connectedDevices) {
      if (device.id.toString() == deviceId) {
        _connectToDevice(device);
        return;
      }
    }
  }
  /// 🔹 블루투스 장치 검색
  void _startScan() async {
    if (_isScanning) {
      print("⚠️ 기존 블루투스 스캔 중단 후 다시 시작");
      await FlutterBluePlus.stopScan();
      await Future.delayed(Duration(milliseconds: 500));
    }

    print("🔍 블루투스 장치 검색 시작...");
    setState(() {
      _isScanning = true;
    });

    FlutterBluePlus.startScan(timeout: const Duration(seconds: 4));

    _scanSubscription?.cancel();
    _scanSubscription = FlutterBluePlus.scanResults.listen((results) {
      if (mounted) {
        setState(() {
          _devicesList = results
              .map((r) => r.device)
              .where((device) => device.name.isNotEmpty)
              .toList();
        });
        print("📡 UI 업데이트 - 검색된 장치: ${_devicesList.map((d) => d.name).toList()}");
      }
    });

    Future.delayed(Duration(seconds: 5), () {
      if (mounted) {
        setState(() {
          _isScanning = false;
        });
        print("✅ 블루투스 스캔 종료. 검색된 장치 수: ${_devicesList.length}");
      }
    });
  }

  /// 🔹 블루투스 프린터 연결 (자동 연결 지원)
  Future<void> _connectToDevice(BluetoothDevice device) async {
    setState(() => _isConnecting = true);
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

      setState(() {
        _selectedDevice = device;
        _isConnecting = false;
        _isConnected = true;
      });

      // ✅ 연결된 프린터 정보 저장 (자동 재연결을 위해)
      SharedPreferences prefs = await SharedPreferences.getInstance();
      await prefs.setString('last_printer_id', device.id.toString());
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("블루투스 연결 실패: 다시 시도하세요.")),
      );
    }
  }

  /// 🔹 한글 영수증을 이미지로 변환하는 함수
  /// 🔹 한글 영수증을 작은 이미지로 변환하는 함수 (이미지 크기 축소)
  Future<Uint8List> _generateReceiptImage() async {
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder);
    const double width = 256;  // 기존보다 축소
    const double height = 80;

    final paint = Paint()..color = Colors.white;
    canvas.drawRect(Rect.fromLTWH(0, 0, width, height), paint);

    final textPainter = TextPainter(
      text: TextSpan(
        text: "테스트 영수증\n----------------\n아이스크림 2개 5,000원\n초콜릿바 1개 2,500원\n----------------\n총: 7,500원",
        style: const TextStyle(color: Colors.black, fontSize: 16),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(10, 10));

    final picture = recorder.endRecording();
    final imgData = await picture.toImage(width.toInt(), height.toInt());
    final byteData = await imgData.toByteData(format: ui.ImageByteFormat.png);

    return byteData!.buffer.asUint8List();
  }

  /// 🔹 블루투스 프린터로 이미지 출력 (작은 조각으로 나눠 전송)
  Future<void> _printReceipt() async {
    if (_writeCharacteristic == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("프린터에 연결되지 않았습니다.")),
      );
      return;
    }

    try {
      Uint8List imageBytes = await _generateReceiptImage();
      List<int> bytes = [0x1D, 0x76, 0x30, 0x00];
      bytes.addAll(imageBytes);

      int chunkSize = 505;  // 최대 전송 크기
      for (int i = 0; i < bytes.length; i += chunkSize) {
        int end = (i + chunkSize < bytes.length) ? i + chunkSize : bytes.length;
        await _writeCharacteristic!.write(Uint8List.fromList(bytes.sublist(i, end)));
        await Future.delayed(Duration(milliseconds: 100));  // 전송 간 딜레이 추가
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("영수증이 출력되었습니다!")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("영수증 출력 실패: 다시 시도하세요.")),
      );
    }
  }

  @override
  void dispose() {
    _scanSubscription?.cancel();
    print("📌 BluetoothPrinterScreen 종료됨");
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("블루투스 프린터 연결")),
      body: Column(
        children: [
          const SizedBox(height: 20),
          Center(
            child: Text(
              _devicesList.isEmpty
                  ? "🔍 검색된 블루투스 장치가 없습니다."
                  : "🔹 검색된 장치 수: ${_devicesList.length}",
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 10),
          _isConnecting
              ? const CircularProgressIndicator()
              : _isConnected
              ? Column(
            children: [
              Text("✅ 연결된 프린터: ${_selectedDevice?.name}"),
              ElevatedButton(
                onPressed: _printReceipt,
                child: const Text("🖨 영수증 출력"),
              ),
            ],
          )
              : Expanded(
            child: _devicesList.isEmpty
                ? const Center(child: Text("⚠️ 검색된 장치 없음"))
                : ListView.builder(
              itemCount: _devicesList.length,
              itemBuilder: (context, index) {
                BluetoothDevice device = _devicesList[index];
                return ListTile(
                  title: Text(device.name.isNotEmpty
                      ? device.name
                      : "이름 없는 기기"),
                  subtitle: Text(device.id.toString()),
                  onTap: () => _connectToDevice(device),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

import 'dart:async';
import 'dart:typed_data';
import 'package:provider/provider.dart';  // ✅ Provider 추가
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:ui' as ui;
import 'package:image/image.dart' as img;
import '../bluetooth_printer_provider.dart';


class BluetoothPrinterDialog  extends StatefulWidget {
  @override
  _BluetoothPrinterDialogState  createState() => _BluetoothPrinterDialogState ();
}

class _BluetoothPrinterDialogState  extends State<BluetoothPrinterDialog > {
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
    List<BluetoothDevice> connectedDevices = await FlutterBluePlus
        .connectedDevices;
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
        print(
            "📡 UI 업데이트 - 검색된 장치: ${_devicesList.map((d) => d.name).toList()}");
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
        for (BluetoothCharacteristic characteristic in service
            .characteristics) {
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
    const double width = 256; // 기존보다 축소
    const double height = 80;

    final paint = Paint()
      ..color = Colors.white;
    canvas.drawRect(Rect.fromLTWH(0, 0, width, height), paint);

    final textPainter = TextPainter(
      text: TextSpan(
        text: "성심유통\n테스트 영수증\n----------------\n아이스크림 2개 5,000원\n초콜릿바 1개 2,500원\n----------------\n총: 7,500원",
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

      int chunkSize = 505; // 최대 전송 크기
      for (int i = 0; i < bytes.length; i += chunkSize) {
        int end = (i + chunkSize < bytes.length) ? i + chunkSize : bytes.length;
        await _writeCharacteristic!.write(
            Uint8List.fromList(bytes.sublist(i, end)));
        await Future.delayed(Duration(milliseconds: 100)); // 전송 간 딜레이 추가
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
    var printerProvider = Provider.of<BluetoothPrinterProvider>(context, listen: false);

    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      elevation: 10,
      backgroundColor: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // ✅ 팝업 제목
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "블루투스 프린터 연결",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.red),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            const Divider(),

            // ✅ 검색 상태 표시
            if (_isConnecting)
              Column(
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 8),
                  const Text("프린터 검색 중..."),
                ],
              )
            else if (_devicesList.isEmpty)
              Column(
                children: [
                  const Icon(Icons.bluetooth_disabled, size: 50, color: Colors.redAccent),
                  const SizedBox(height: 8),
                  const Text("🔍 검색된 블루투스 장치가 없습니다."),
                ],
              )
            else
              Column(
                children: [
                  const Text(
                    "🔹 검색된 장치",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    height: 200,
                    child: ListView.builder(
                      shrinkWrap: true,
                      itemCount: _devicesList.length,
                      itemBuilder: (context, index) {
                        BluetoothDevice device = _devicesList[index];
                        return Card(
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          child: ListTile(
                            leading: const Icon(Icons.print, color: Colors.blueAccent),
                            title: Text(device.name.isNotEmpty ? device.name : "이름 없는 기기"),
                            subtitle: Text(device.id.toString()),
                            onTap: () {
                              _connectToDevice(device); // ✅ 기기 연결
                              printerProvider.connectToDevice(device); // ✅ Provider에 저장
                            },
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),

            const SizedBox(height: 16),

            // ✅ 연결된 프린터 표시
            if (_isConnected)
              Column(
                children: [
                  Text(
                    "✅ 연결된 프린터: ${_selectedDevice?.name}",
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.green),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.check),
                    label: const Text("연결 완료"),
                  ),
                ],
              ),

            const SizedBox(height: 8),

            // ✅ 항상 "재검색" 버튼을 유지 (검색된 장치가 있어도 표시)
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orangeAccent,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              onPressed: _startScan, // ✅ 재검색 버튼 추가
              icon: const Icon(Icons.refresh),
              label: const Text("재검색"),
            ),

            const SizedBox(height: 8),

            // ✅ 검색 중일 때만 "닫기" 버튼 표시
            if (_isConnecting)
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text("닫기", style: TextStyle(color: Colors.red, fontSize: 16)),
              ),
          ],
        ),
      ),
    );
  }
}
  /// 🔹 팝업을 띄우는 함수 (설정 화면에서 사용)
void showBluetoothPrinterDialog(BuildContext context) {
  showDialog(
    context: context,
    builder: (BuildContext context) {
      return BluetoothPrinterDialog();
    },
  );
}
import 'dart:async';
import 'dart:typed_data';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:ui' as ui;
import 'package:image/image.dart' as img;
import '../bluetooth_printer_provider.dart';

class BluetoothPrinterDialog extends StatefulWidget {
  @override
  _BluetoothPrinterDialogState createState() => _BluetoothPrinterDialogState();
}

class _BluetoothPrinterDialogState extends State<BluetoothPrinterDialog> {
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
    _startScan();
  }

  Future<void> _loadLastDevice() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? lastDeviceId = prefs.getString('last_printer_id');
    if (lastDeviceId != null) {
      _attemptReconnect(lastDeviceId);
    }
  }

  Future<void> _attemptReconnect(String deviceId) async {
    final all = await FlutterBluePlus.connectedDevices;
    for (final device in all) {
      if (device.id.toString() == deviceId) {
        await _connectToDevice(device);
        return;
      }
    }

    // 연결되어 있지 않으면 스캔된 장치 중에서 다시 연결 시도
    FlutterBluePlus.startScan(timeout: Duration(seconds: 3));
    FlutterBluePlus.scanResults.listen((results) {
      for (final result in results) {
        if (result.device.id.toString() == deviceId) {
          _connectToDevice(result.device);
          FlutterBluePlus.stopScan();
          break;
        }
      }
    });
  }

  void _startScan() async {
    if (_isScanning) await FlutterBluePlus.stopScan();
    setState(() => _isScanning = true);

    _scanSubscription = FlutterBluePlus.scanResults.listen((results) {
      if (mounted) {
        setState(() {
          _devicesList = results
              .map((r) => r.device)
              .where((d) => d.name.isNotEmpty)
              .toList();
        });
      }
    });

    FlutterBluePlus.startScan(timeout: Duration(seconds: 4));

    Future.delayed(Duration(seconds: 5), () {
      if (mounted) setState(() => _isScanning = false);
    });
  }

  Future<void> _connectToDevice(BluetoothDevice device) async {
    final printerProvider = context.read<BluetoothPrinterProvider>();

    setState(() {
      _isConnecting = true;
      _isConnected = false;
    });

    try {
      await device.connect(autoConnect: false);
      List<BluetoothService> services = await device.discoverServices();

      for (BluetoothService service in services) {
        for (BluetoothCharacteristic c in service.characteristics) {
          if (c.properties.write) {
            _writeCharacteristic = c;
            break;
          }
        }
      }

      _selectedDevice = device;
      _isConnected = true;

      SharedPreferences prefs = await SharedPreferences.getInstance();
      await prefs.setString('last_printer_id', device.id.toString());

      // 🔔 Provider에 연결 상태 업데이트
      printerProvider.connectToDevice(device);

      setState(() {
        _isConnecting = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("${device.name} 연결 성공")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("프린터 연결 실패: $e")),
      );
    } finally {
      setState(() => _isConnecting = false);
    }
  }

  Future<Uint8List> _generateReceiptImage() async {
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder);
    const width = 256.0, height = 100.0;

    final paint = Paint()..color = Colors.white;
    canvas.drawRect(Rect.fromLTWH(0, 0, width, height), paint);

    final textPainter = TextPainter(
      text: TextSpan(
        text: "성심유통\n테스트 영수증\n----------------\n아이스크림 2개 5,000원\n초콜릿바 1개 2,500원\n----------------\n총: 7,500원",
        style: TextStyle(color: Colors.black, fontSize: 14),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(10, 10));

    final picture = recorder.endRecording();
    final img = await picture.toImage(width.toInt(), height.toInt());
    final byteData = await img.toByteData(format: ui.ImageByteFormat.png);

    return byteData!.buffer.asUint8List();
  }

  Future<void> _printReceipt() async {
    if (_writeCharacteristic == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("프린터에 연결되지 않았습니다.")),
      );
      return;
    }

    try {
      final image = await _generateReceiptImage();
      List<int> command = [0x1D, 0x76, 0x30, 0x00];
      command.addAll(image);

      for (int i = 0; i < command.length; i += 500) {
        final chunk = command.sublist(i, i + 500 > command.length ? command.length : i + 500);
        await _writeCharacteristic!.write(Uint8List.fromList(chunk));
        await Future.delayed(Duration(milliseconds: 100));
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("영수증 출력 완료!")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("인쇄 실패: $e")),
      );
    }
  }

  @override
  void dispose() {
    _scanSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final printerProvider = context.watch<BluetoothPrinterProvider>();

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("프린터 연결", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                IconButton(
                  icon: Icon(Icons.close, color: Colors.red),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const Divider(),
            if (_isConnecting)
              Column(
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 8),
                  Text("연결 중..."),
                ],
              )
            else if (_devicesList.isEmpty)
              Text("🔍 검색된 장치 없음")
            else
              SizedBox(
                height: 200,
                child: ListView.builder(
                  itemCount: _devicesList.length,
                  itemBuilder: (_, i) {
                    final d = _devicesList[i];
                    return ListTile(
                      leading: Icon(Icons.print),
                      title: Text(d.name),
                      subtitle: Text(d.id.toString()),
                      onTap: () => _connectToDevice(d),
                    );
                  },
                ),
              ),
            SizedBox(height: 16),
            if (_isConnected && _selectedDevice != null)
              Column(
                children: [
                  Text("✅ 연결됨: ${_selectedDevice!.name}"),
                  SizedBox(height: 8),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.pop(context),
                    icon: Icon(Icons.check),
                    label: Text("확인"),
                  )
                ],
              ),
            ElevatedButton.icon(
              onPressed: _startScan,
              icon: Icon(Icons.refresh),
              label: Text("재검색"),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            )
          ],
        ),
      ),
    );
  }
}

void showBluetoothPrinterDialog(BuildContext context) {
  showDialog(
    context: context,
    builder: (_) => BluetoothPrinterDialog(),
  );
}

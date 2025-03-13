import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class BarcodeScannerPage extends StatefulWidget {
  const BarcodeScannerPage({super.key});

  @override
  State<BarcodeScannerPage> createState() => _BarcodeScannerPageState();
}

class _BarcodeScannerPageState extends State<BarcodeScannerPage> {
  final MobileScannerController _controller = MobileScannerController();
  bool _hasPopped = false; // 중복 pop 방지 플래그

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _toggleFlash() {
    _controller.toggleTorch();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("바코드 스캔"),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: _toggleFlash,
          ),
        ],
      ),
      body: MobileScanner(
        controller: _controller,
        onDetect: (BarcodeCapture capture) {
          final List<Barcode> barcodes = capture.barcodes;
          if (barcodes.isNotEmpty) {
            final String code = barcodes.first.rawValue ?? "";
            if (code.isNotEmpty && !_hasPopped) {
              _hasPopped = true; // 중복 pop 방지
              Navigator.pop(context, code);
            }
          }
        },
      ),
    );
  }
}

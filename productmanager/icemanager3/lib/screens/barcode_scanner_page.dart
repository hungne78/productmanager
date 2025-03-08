import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class BarcodeScannerPage extends StatefulWidget {
  const BarcodeScannerPage({super.key});

  @override
  State<BarcodeScannerPage> createState() => _BarcodeScannerPageState();
}

class _BarcodeScannerPageState extends State<BarcodeScannerPage> {
  final MobileScannerController _controller = MobileScannerController();

  /// 이미 스캔 결과를 처리했는지 여부를 표시하기 위한 플래그
  bool _hasPopped = false;

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
          // 플래시 토글 버튼
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: _toggleFlash,
          ),
        ],
      ),
      body: MobileScanner(
        controller: _controller,
        onDetect: (barcode, args) {
          final String code = barcode.rawValue ?? "";
          if (code.isNotEmpty && !_hasPopped) {
            // 이미 pop된 적이 없으면 처리
            _hasPopped = true; // 중복 pop 방지
            Navigator.pop(context, code);
          }
        },
      ),
    );
  }
}

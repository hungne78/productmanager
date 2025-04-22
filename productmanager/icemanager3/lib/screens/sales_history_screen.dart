import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart' as BLE;
import 'package:image/image.dart' as img;
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:flutter/widgets.dart' as widgets;
import '../auth_provider.dart';
import '../bluetooth_printer_provider.dart';
import '../services/api_service.dart';
import 'home_screen.dart';
import 'package:shared_preferences/shared_preferences.dart'; // 설정 저장

/// 📄 판매 내역 조회 + 출력 화면
/// ---------------------------------------------------------------------------
/// * 날짜 하나를 선택해서 당일 판매를 불러온다.
/// * 거래처·상품별 목록 → 합계(박스·금액) 표시
/// * 하단 프린터 버튼으로 55 / 80 mm 영수증 인쇄
class SalesHistoryScreen extends StatefulWidget {
  final String token;
  final DateTime selectedDate;

  const SalesHistoryScreen({
    Key? key,
    required this.token,
    required this.selectedDate,
  }) : super(key: key);

  @override
  State<SalesHistoryScreen> createState() => _SalesHistoryScreenState();
}

class _SalesHistoryScreenState extends State<SalesHistoryScreen> {
  final List<Map<String, dynamic>> _sales = [];
  final formatter = NumberFormat('#,###');

  /// 합계
  int _totalBoxes = 0;
  int _totalAmount = 0;

  /// 프린터
  String _printerPaperSize = '80mm'; // SharedPreferences 에서 불러오도록 해도 됨
  String _printerLanguage = 'non-korean';
  bool _isPrinterConnected = false;

  @override
  void initState() {
    super.initState();
    _fetchSales();
    _listenPrinterState();
  }

  /// -------------------------------------------------------------------------
  /// 1. 서버에서 판매 내역 가져오기
  /// -------------------------------------------------------------------------
  Future<void> _fetchSales() async {
    try {
      final auth = context.read<AuthProvider>();
      final int employeeId = auth.user?.id ?? 0;
      final String dateStr = widget.selectedDate.toIso8601String().substring(0, 10);

      // ✅ 수정된 API 호출
      final resp = await ApiService.fetchSalesDetailsByDate(
        widget.token,
        employeeId,
        dateStr,
      ); // FastAPI /sales/details/{employee_id}/{date}

      if (resp.statusCode != 200) {
        throw ('${resp.statusCode} / ${resp.body}');
      }

      final List<dynamic> data = jsonDecode(resp.body);

      setState(() {
        _sales
          ..clear()
          ..addAll(data.cast<Map<String, dynamic>>());

        // ✅ 총 박스수 & 총 금액은 상품 단위로 직접 계산
        _totalBoxes = _sales.fold<int>(0, (sum, e) {
          return sum + ((e['total_boxes'] ?? 0) as num).toInt();
        });

        _totalAmount = _sales.fold<int>(0, (sum, e) {
          return sum + ((e['total_sales'] ?? 0) as num).toInt();
        });
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('판매 내역을 불러오지 못했습니다 → $e')),
      );
    }
  }

  /// -------------------------------------------------------------------------
  /// 2. UI
  /// -------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        title: Text(
          '판매 내역 (${widget.selectedDate.toLocal().toString().split(' ')[0]})',
        ),
        leading: IconButton(
          icon: const Icon(Icons.home),
          onPressed: () => Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(builder: (_) => HomeScreen(token: widget.token)),
                (_) => false,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.print),
            onPressed: _isPrinterConnected ? _printReceiptImageFlexible : null,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(child: _buildSalesList()),
          _buildSummaryBar(),
        ],
      ),
    );
  }

  /// -------------------------------------------------------------------------
  /// 2‑1. 판매 목록을 Table → ListView.builder 로 변경
  /// -------------------------------------------------------------------------
  Widget _buildSalesList() {
    if (_sales.isEmpty) {
      return const Center(child: Text('데이터가 없습니다.'));
    }

    final headerStyle = TextStyle(
      fontWeight: FontWeight.bold,
      color: Colors.grey.shade700,
    );

    // 헤더 + 목록을 하나의 Column 으로 묶고, 목록은 Expanded 된 ListView.builder 로 스크롤 처리
    return Column(
      children: [
        // 헤더
        Container(
          color: Colors.grey.shade300,
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
          child: Row(
            children: [
              _headerCell('거래처', flex: 3, style: headerStyle),
              _headerCell('박스', flex: 2, style: headerStyle, align: TextAlign.center),
              _headerCell('금액', flex: 3, style: headerStyle, align: TextAlign.right),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _sales.length,
            itemBuilder: (context, index) {
              final e = _sales[index];
              final client = e['client_name'] ?? '';
              final isReturn = e['is_return'] == true;

              final totalBoxes = (e['total_boxes'] ?? 0).abs();
              final totalSales = (e['total_sales'] ?? 0).abs();

              final bgColor = isReturn ? Colors.red.shade50 : Colors.white;

              return Container(
                color: bgColor,
                padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
                child: Row(
                  children: [
                    _dataCell(client + (isReturn ? ' (반품)' : ''), flex: 3),
                    _dataCell(totalBoxes.toString(), flex: 2, align: TextAlign.center),
                    _dataCell('${formatter.format(totalSales)}원', flex: 3, align: TextAlign.right),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  /// Cell helpers -----------------------------------------------------------
  Widget _headerCell(String text, {required int flex, required TextStyle style, TextAlign align = TextAlign.left}) {
    return Expanded(
      flex: flex,
      child: Text(text, style: style, textAlign: align),
    );
  }

  Widget _dataCell(String text, {required int flex, TextAlign align = TextAlign.left}) {
    return Expanded(
      flex: flex,
      child: Text(text, textAlign: align),
    );
  }

  /// -------------------------------------------------------------------------
  /// 2‑2. Summary bar
  /// -------------------------------------------------------------------------
  Widget _buildSummaryBar() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey)),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4)],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _sumCell('총 박스', formatter.format(_totalBoxes)),
          _sumCell('총 금액', '${formatter.format(_totalAmount)}원'),
        ],
      ),
    );
  }

  Widget _sumCell(String label, String value) => Column(
    children: [
      Text(label, style: const TextStyle(fontSize: 13, color: Colors.grey)),
      const SizedBox(height: 4),
      Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
    ],
  );

  /// -------------------------------------------------------------------------
  /// 3. 프린터 연결 상태 모니터링
  /// -------------------------------------------------------------------------
  void _listenPrinterState() {
    final printer = context.read<BluetoothPrinterProvider>();
    _isPrinterConnected = printer.isConnected;
    printer.addListener(() {
      if (mounted) {
        setState(() => _isPrinterConnected = printer.isConnected);
      }
    });
  }

  Future<BLE.BluetoothCharacteristic?> _getConnectedPrinterWriteCharacteristic() async {
    final prefs = await SharedPreferences.getInstance();
    String? printerId = prefs.getString('last_printer_id');
    if (printerId == null) return null;

    final connectedDevices = await BLE.FlutterBluePlus.connectedDevices;
    final device = connectedDevices.firstWhere(
          (d) => d.id.toString() == printerId,
      orElse: () => throw Exception('연결된 프린터를 찾을 수 없습니다.'),
    );

    final services = await device.discoverServices();
    for (var s in services) {
      for (var c in s.characteristics) {
        if (c.properties.write) {
          return c; // ✅ 첫 번째 write characteristic 반환
        }
      }
    }
    return null; // 못 찾으면 null
  }

  /// 이미지 이진화(흑백 처리) 함수 ------------------------------------------------
  img.Image threshold(img.Image src, {int threshold = 160}) {
    final output = img.Image.from(src);
    for (int y = 0; y < output.height; y++) {
      for (int x = 0; x < output.width; x++) {
        final pixel = output.getPixel(x, y);
        final luma = img.getLuminance(pixel); // 밝기 계산
        if (luma < threshold) {
          output.setPixelRgba(x, y, 0, 0, 0, 255); // 어두우면 검정
        } else {
          output.setPixelRgba(x, y, 255, 255, 255, 255); // 밝으면 흰색
        }
      }
    }
    return output;
  }

  /// -------------------------------------------------------------------------
  /// 4. 55/80 mm 영수증 이미지 생성 → ESC/POS 전송
  /// -------------------------------------------------------------------------
  Future<void> _printReceiptImageFlexible() async {
    try {
      final writeChar = await _getConnectedPrinterWriteCharacteristic();
      if (writeChar == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('⚠️ 프린터가 연결되지 않았습니다.')),
        );
        return;
      }

      final Map<String, dynamic>? company = await ApiService.fetchCompanyInfo(widget.token);
      if (company == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('회사 정보를 불러올 수 없습니다.')),
        );
        return;
      }

      final Uint8List pngBytes = await _generateReceiptImage(company);
      final decoded = img.decodeImage(pngBytes);
      if (decoded == null) throw ('디코딩 실패');

      final gray = img.grayscale(decoded);
      final bw = threshold(gray);

      final profile = await CapabilityProfile.load();
      final paper = _printerPaperSize == '55mm' ? PaperSize.mm58 : PaperSize.mm80;
      final gen = Generator(paper, profile);

      final ticket = <int>[];
      ticket.addAll(gen.image(bw));
      ticket.addAll(gen.feed(1));
      ticket.addAll(gen.cut());

      const chunk = 200;
      for (int i = 0; i < ticket.length; i += chunk) {
        await writeChar.write(ticket.sublist(i, i + chunk > ticket.length ? ticket.length : i + chunk), withoutResponse: true);
        await Future.delayed(const Duration(milliseconds: 30));
      }

      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('✅ 인쇄 완료')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('인쇄 실패 → $e')));
    }
  }

  /// 4‑1. Canvas → PNG 생성 -----------------------------------------------------
  Future<Uint8List> _generateReceiptImage(Map<String, dynamic> company) async {
    const double canvasWidth = 576; // 80 mm 기준
    final textPainter = TextPainter(textDirection: widgets.TextDirection.ltr, maxLines: null);

    final now = DateFormat('yyyy‑MM‑dd HH:mm').format(DateTime.now());
    String _line() => '━' * 35;

    String receipt = '[영수증]\n${_line()}\n날짜: $now\n${company['company_name']}   대표: ${company['ceo_name']}\n${company['address']}\nTel: ${company['phone']}\n사업자번호: ${company['business_number']}\n${_line()}\n상품명      박스수    합  계\n${_line()}\n';

    for (var e in _sales) {
      receipt += _formatRow(e['client_name'], e['total_boxes'], e['total_sales']);
    }

    receipt += '\n${_line()}\n총 박스: $_totalBoxes\n총 금액: ${formatter.format(_totalAmount)} 원\n${_line()}\n';

    textPainter.text = TextSpan(text: receipt, style: const TextStyle(fontFamily: 'Courier', fontSize: 26));
    textPainter.layout(maxWidth: canvasWidth - 20);

    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder)..drawColor(Colors.white, BlendMode.src);
    textPainter.paint(canvas, const Offset(10, 10));

    final pic = recorder.endRecording();
    final imgBytes = await (await pic.toImage(canvasWidth.toInt(), textPainter.height.toInt() + 20)).toByteData(format: ui.ImageByteFormat.png);

    return imgBytes!.buffer.asUint8List();
  }

  String _formatRow(dynamic client, dynamic boxes, dynamic sales) {
    final clientName = (client ?? '').toString();
    final boxText = (boxes ?? 0).toString();
    final salesText = formatter.format(sales ?? 0);

    return '${_padRight(clientName, 10)} ${_padLeft(boxText, 6)} ${_padLeft(salesText, 12)}\n';
  }

  /// utils -------------------------------------------------------------------
  int _textWidth(String s) => s.runes.fold<int>(0, (p, c) => p + (c > 0x7f ? 2 : 1));

  String _padRight(String s, int n) {
    final diff = n - _textWidth(s);
    return diff > 0 ? '$s${' ' * diff}' : s;
  }

  String _padLeft(String s, int n) {
    final diff = n - _textWidth(s);
    return diff > 0 ? '${' ' * diff}$s' : s;
  }
}

class SalesHistoryArgs {
  final String token;
  final Map<String, dynamic> client;
  final DateTime date;

  SalesHistoryArgs({
    required this.token,
    required this.client,
    required this.date,
  });
}

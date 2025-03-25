import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';
import '../auth_provider.dart';
import 'barcode_scanner_page.dart';
import '../user.dart';
import 'package:provider/provider.dart';  // ✅ Provider 패키지 추가
import '../product_provider.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:intl/intl.dart'; // ✅ 숫자 포맷을 위한 패키지 추가
import 'dart:developer' as developer;
import 'package:flutter/services.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart'as spp; // SPP 모드
import 'package:flutter_blue_plus/flutter_blue_plus.dart' as BLE;// BLE 모드
import 'package:shared_preferences/shared_preferences.dart'; // 설정 저장
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:async'; // ✅ 비동기 Stream 관련 클래스 포함
import 'package:permission_handler/permission_handler.dart';
import '../screens/home_screen.dart';
import '../screens/printer.dart'; // 경로는 프로젝트에 맞게 조정
import 'dart:ui' as ui;
import 'package:flutter/widgets.dart' as widgets;
import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';
import 'package:image/image.dart' as img;
import 'package:url_launcher/url_launcher.dart';
import '../bluetooth_printer_provider.dart';

AndroidDeviceInfo? androidInfo;

class SalesScreen extends StatefulWidget {
  final String token;
  final Map<String, dynamic> client; // 거래처 정보

  const SalesScreen({Key? key, required this.token, required this.client}) : super(key: key);

  @override
  _SalesScreenState createState() => _SalesScreenState();
}


class _SalesScreenState extends State<SalesScreen> with WidgetsBindingObserver {
  late Map<String, dynamic> client; // ✅ 변경 가능하도록 설정
  late TextEditingController paymentController;
  late FocusNode paymentFocusNode;

  bool _isClientInfoExpanded = false;

  bool _isBluetoothConnected = false;
  String? _connectedDeviceName;
  spp.BluetoothConnection? _bluetoothConnection; // SPP 모드 블루투스 연결
  StreamSubscription<Uint8List>? _inputSubscription;
  bool _isConnecting = false;

  String _barcodeBuffer = ''; // 바코드 누적 버퍼
  final FocusNode _keyboardFocusNode = FocusNode(); // HID 모드 감지
  final MobileScannerController _cameraScanner = MobileScannerController(); // 카메라 바코드 스캔

  String _scannerMode = "HID"; // 기본 HID 모드

  double totalScannedItemsPrice = 0.0;
  double totalReturnedItemsPrice = 0.0;
  final formatter = NumberFormat("#,###"); // ✅ 천단위 콤마 포맷 설정

  List<Map<String, dynamic>> _returnedItems = []; // ✅ 반품 상품 리스트

  bool _isReturnMode = false; // ✅ 기본값: 판매 모드 (반품 모드가 아님)

  dynamic _selectedClient;
  List<Map<String, dynamic>> _scannedItems = []; // 스캔된 품목 리스트
  int? selectedIndex; // ✅ 선택된 행의 인덱스 저장
  bool _isLoading = false;
  String? _error;


  //프린터 관련
  String _printerPaperSize = '80mm';
  String _printerLanguage = 'non-korean';

  bool _isPrinterConnected = false; // 초기값

  @override
  void initState() {
    super.initState();
    // _tryAutoReconnect();
    _loadScannerMode();
    _loadDeviceInfo();
    _checkBluetoothPermissions(); // ✅ 필수
    // _initializeSPP(); // SPP 모드 초기화
    _initializeBLE(); // BLE 모드 초기화
    _checkPrinterConnection(); // 연결 여부 확인
    _loadPrinterSettings(); // ✅ 프린터 설정값 로딩
    WidgetsBinding.instance.addObserver(this);

    client = Map<String, dynamic>.from(widget.client); // client 초기화
    paymentController = TextEditingController(text: ""); // 입금 금액 기본값 빈 문자열로 설정
    paymentFocusNode = FocusNode(); // 포커스 노드 초기화
    _selectedClient = widget.client; // 거래처 정보 설정
    // ✅ 상품 목록 확인 및 필요 시 업데이트
    _selectedClient = widget.client;
    // ...
    final printerProvider = context.read<BluetoothPrinterProvider>();
    printerProvider.loadLastDevice(); // 자동 재연결 시도

    // 프린터 연결 상태 반영
    printerProvider.addListener(() {
      final isConnected = printerProvider.isConnected;
      if (mounted) {
        setState(() {
          _isPrinterConnected = isConnected;
        });
      }
    });


    // ✅ ProductProvider에서 상품 목록을 가져오도록 설정
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final productProvider = context.read<ProductProvider>();

      // ✅ 상품 목록이 비어 있으면 다시 가져오기
      if (productProvider.products.isEmpty) {
        print("⚠️ SalesScreen: 상품 목록이 비어 있음. 서버에서 다시 불러옴.");
        final List<dynamic> products = await ApiService.fetchAllProducts(widget.token);
        if (products.isNotEmpty) {
          productProvider.setProducts(List<Map<String, dynamic>>.from(products));
          print("✅ SalesScreen: 상품 목록 업데이트 완료. 총 ${products.length}개");
        } else {
          print("❌ SalesScreen: 서버에서 상품을 가져오지 못함.");
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("상품 목록을 가져오지 못했습니다.")),
          );
        }
      } else {
        print("✅ SalesScreen: ProductProvider에서 상품을 정상적으로 가져옴. 총 ${productProvider.products.length}개");
      }
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // 여기서 _keyboardFocusNode를 실제로 포커스하도록
      _tryReconnectToPrinter();
      FocusScope.of(context).requestFocus(_keyboardFocusNode);
      _tryReconnectToLastDeviceOnEntry();
    });

  }
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cameraScanner.dispose();
    _inputSubscription?.cancel();
    _bluetoothConnection?.finish();
    WidgetsBinding.instance.removeObserver(this);
    paymentController.dispose();
    paymentFocusNode.dispose();
    super.dispose();
  }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      print("🔄 앱이 다시 포그라운드로 돌아옴");

      // 강제로 연결 상태 초기화 (안드로이드 SPP 안전용)
      _inputSubscription?.cancel();
      _bluetoothConnection?.finish();
      _bluetoothConnection = null;
      _inputSubscription = null;

      setState(() {
        _isBluetoothConnected = false;
        _connectedDeviceName = null;
      });

      // 자동으로 최근 장치로 재연결 시도 (선택)
      Future.delayed(Duration(seconds: 1), () {
        _tryReconnectToLastDevice(); // 👇 아래에서 만들자
      });
    }
  }
  Future<void> _tryReconnectToPrinter() async {
    final prefs = await SharedPreferences.getInstance();
    final lastPrinterId = prefs.getString('last_printer_id');
    if (lastPrinterId == null) return;

    try {
      final devices = await BLE.FlutterBluePlus.connectedDevices;
      final target = devices.firstWhere(
            (d) => d.id.toString() == lastPrinterId,
        orElse: () => throw Exception("최근 프린터를 찾을 수 없습니다."),
      );

      await target.connect(); // 이미 연결되었더라도 예외 없이 처리됨
      final services = await target.discoverServices();
      final hasWriteCharacteristic = services.any((s) =>
          s.characteristics.any((c) => c.properties.write));

      if (hasWriteCharacteristic) {
        print("✅ 프린터 자동 재연결 완료");
        setState(() => _isPrinterConnected = true);
      } else {
        setState(() => _isPrinterConnected = false);
      }
    } catch (e) {
      print("❌ 프린터 자동 재연결 실패: $e");
      setState(() => _isPrinterConnected = false);
    }
  }

  Future<void> _loadPrinterSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _printerPaperSize = prefs.getString('printer_paper_size') ?? '80mm';
      _printerLanguage = prefs.getString('printer_language') ?? 'non-korean';
    });
  }

  Future<void> _checkPrinterConnection() async {
    final prefs = await SharedPreferences.getInstance();
    String? printerId = prefs.getString('last_printer_id');

    if (printerId == null) {
      setState(() => _isPrinterConnected = false);
      return;
    }

    final connectedDevices = await BLE.FlutterBluePlus.connectedDevices;
    bool found = connectedDevices.any((d) => d.id.toString() == printerId);
    setState(() => _isPrinterConnected = found);
  }

  Future<void> debugPrintAllWriteCharacteristics() async {
    final prefs = await SharedPreferences.getInstance();
    String? printerId = prefs.getString('last_printer_id');
    if (printerId == null) {
      print("❌ 프린터 ID 없음");
      return;
    }

    final devices = await BLE.FlutterBluePlus.connectedDevices;
    final device = devices.firstWhere(
          (d) => d.id.toString() == printerId,
      orElse: () => throw Exception("❌ 연결된 프린터를 찾을 수 없습니다."),
    );

    final services = await device.discoverServices();
    print("🔍 전체 서비스 및 write 가능한 특성 탐색 시작");

    for (var s in services) {
      for (var c in s.characteristics) {
        if (c.properties.write) {
          print("✅ [WRITE] UUID: ${c.uuid.toString().toLowerCase()}");
        }
      }
    }

    print("🔚 탐색 완료");
  }
  //  BLE 스캐너 자동 탐색 (UUID 자동)
  Future<void> autoDetectScanner(BLE.BluetoothDevice device) async {
    print("🔍 [autoDetectScanner] BLE 스캐너 자동 탐색 시작: ${device.name}");
    // 이미 연결되었다면 중복 connect 에러가 안나도록 예외처리
    if (device.state != BLE.BluetoothDeviceState.connected) {
      await device.connect(autoConnect: false);
    }

    final services = await device.discoverServices();

    bool foundScanner = false;

    // notify Characteristic 찾아 시도
    for (var service in services) {
      for (var characteristic in service.characteristics) {
        if (characteristic.properties.notify) {
          print("✅ 후보 Notify Characteristic: ${characteristic.uuid}");

          // notify 활성화
          await characteristic.setNotifyValue(true);

          bool gotBarcode = false;
          StreamSubscription? subscription;

          subscription = characteristic.value.listen((value) {
            try {
              final data = utf8.decode(value);
              print("📦 스캐너 UTF-8 데이터: $data");
            } catch (e) {
              final asciiData = value.map((b) => String.fromCharCode(b)).join();
              print("⚠️ UTF-8 실패, ASCII로 해석: $asciiData");
            }
          });
          // 3초 대기 -> 바코드 들어오면 성공 처리
          await Future.delayed(Duration(seconds: 3));

          // Notify 해제
          await characteristic.setNotifyValue(false);
          await subscription?.cancel();

          if (gotBarcode) {
            print("🎉 유효 스캐너 UUID 감지: ${characteristic.uuid}");
            // 필요시 SharedPreferences 등에 저장 가능
            break;
          }
        }

        if (foundScanner) break; // 스캐너 찾으면 반복 중단
      }
      if (foundScanner) break;
    }

    if (!foundScanner) {
      print("❌ 스캐너로 쓸 만한 Notify Characteristic을 찾지 못했습니다.");
    }
  }

  Future<BLE.BluetoothCharacteristic?> _getConnectedPrinterWriteCharacteristic() async {
    final prefs = await SharedPreferences.getInstance();
    String? printerId = prefs.getString('last_printer_id');
    if (printerId == null) return null;

    // 이미 연결된 디바이스 중 찾아보기
    final connectedDevices = await BLE.FlutterBluePlus.connectedDevices;
    final device = connectedDevices.firstWhere(
          (d) => d.id.toString() == printerId,
      orElse: () => throw Exception("연결된 프린터를 찾을 수 없습니다."),
    );

    // [신규 로직] 자동 탐색
    final writeChar = await autoDetectPrinter(device);
    return writeChar; // 못 찾으면 null
  }




  Future<void> _checkBluetoothPermissions() async {
    if (await Permission.bluetoothScan.request().isGranted &&
        await Permission.bluetoothConnect.request().isGranted &&
        await Permission.location.request().isGranted) {
      print("✅ 블루투스 권한 허용됨");
    } else {
      Fluttertoast.showToast(msg: "⚠️ 블루투스 권한이 필요합니다.");
    }
  }

  Future<void> _tryReconnectToLastDeviceOnEntry() async {
    if (_isConnecting || (_bluetoothConnection?.isConnected ?? false)) {
      print("⏸ 이미 연결 중이거나 연결됨 → 재연결 생략");
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final address = prefs.getString('last_device_address');

    if (address == null) {
      print("⚠️ 이전 연결 기기 주소 없음");
      return;
    }

    final dummyDevice = spp.BluetoothDevice(name: "최근기기", address: address);
    print("🔁 최근 연결된 기기로 재연결 시도: $address");
    await _connectToDevice(dummyDevice);
  }

  Future<void> _tryReconnectToLastDevice() async {
    final prefs = await SharedPreferences.getInstance();
    final address = prefs.getString('last_device_address');

    if (address == null) return;

    final dummyDevice = spp.BluetoothDevice(name: "최근기기", address: address);
    await _connectToDevice(dummyDevice);
  }

  /// 📌 저장된 바코드 스캔 모드 불러오기
  Future<void> _loadScannerMode() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _scannerMode = prefs.getString('scanner_mode') ?? "HID";
    });
  }
  Future<void> _loadDeviceInfo() async {
    final deviceInfoPlugin = DeviceInfoPlugin();
    androidInfo = await deviceInfoPlugin.androidInfo;
    print("📱 기기 모델: ${androidInfo?.model}");
  }
  bool isGalaxyFold() {
    const foldModels = [
      "SM-F900", // Fold 1
      "SM-F916", // Fold 2
      "SM-F926", // Fold 3
      "SM-F936", // Fold 4
      "SM-F946", // Fold 5
    ];

    final model = androidInfo?.model ?? '';
    return foldModels.any((m) => model.contains(m));
  }
  // [신규] BLE 프린터 자동 탐색 예시
  Future<BLE.BluetoothCharacteristic?> autoDetectPrinter(BLE.BluetoothDevice device) async {
    print("🔍 [autoDetectPrinter] BLE 프린터 자동 탐색 시작: ${device.name}");
    if (device.state != BLE.BluetoothDeviceState.connected) {
      await device.connect();
    }

    final services = await device.discoverServices();
    BLE.BluetoothCharacteristic? foundWriteChar;

    for (var s in services) {
      for (var c in s.characteristics) {
        if (c.properties.write) {
          print("✅ 후보 WRITE Characteristic: ${c.uuid}");

          // [테스트] "Hello Printer" 데이터를 써보고 에러 없으면 성공으로 간주
          try {
            await c.write(utf8.encode("Hello Printer Test\n"));
            print("🎉 프린터 WRITE 성공 -> Characteristic: ${c.uuid}");
            foundWriteChar = c;
            // 여기서 SharedPreferences 등에 c.uuid 저장 가능
            break;
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
  /// 📌 SPP 모드 초기화 (Bluetooth Serial)
  Future<void> _initializeSPP() async {
    List<spp.BluetoothDevice> devices = await spp.FlutterBluetoothSerial.instance.getBondedDevices();

    if (devices.isNotEmpty) {
      spp.BluetoothDevice selectedDevice = devices.first; // 첫 번째 페어링된 장치 사용 (실제 앱에서는 UI에서 선택하도록 구현)

      spp.BluetoothConnection.toAddress(selectedDevice.address).then((connection) {
        setState(() => _bluetoothConnection = connection);
        connection.input?.listen((Uint8List data) {
          String barcode = String.fromCharCodes(data);
          _handleBarcode(barcode);
        });
      }).catchError((error) {
        print("⚠️ SPP 연결 실패: $error");
      });
    } else {
      print("❌ 페어링된 블루투스 장치가 없습니다.");
    }
  }
  void _showBluetoothPrinterDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return BluetoothPrinterDialog(); // ✅ printer.dart에 정의된 다이얼로그
      },
    );
  }


  /// 📌 BLE 모드 초기화
  void _initializeBLE() {
    BLE.FlutterBluePlus.startScan(timeout: Duration(seconds: 5));

    // [수정] 모든 ScanResult에 대해 스캐너 후보로 시도
    BLE.FlutterBluePlus.scanResults.listen((results) async {
      for (BLE.ScanResult r in results) {
        final device = r.device;
        // 예: 원하면 이름이나 RSSI 필터를 걸 수도 있음
        // if (device.name.isEmpty) continue;
        try {
          await device.connect(autoConnect: false);
        } catch (e) {
          print("❌ 연결 실패: $e");
          await device.disconnect(); // 실패하더라도 disconnect 시도
        }
        // 스캐너 자동탐색 시도
        await autoDetectScanner(device);
      }
    });
  }

  // 상품을 클릭하여 선택된 인덱스를 저장
  void _selectItem(int index) {
    setState(() {
      selectedIndex = index; // 선택된 상품의 인덱스를 저장
    });
  }
  String preprocessBarcode(String raw) {
    // 공백 및 특수 문자 제거 (SPP 대비)
    String cleaned = raw
        .replaceAll(RegExp(r'[^0-9A-Za-z]'), '') // 숫자/영문 외 제거
        .replaceAll(RegExp(r'^[Nn]'), '') // 앞에 N 제거
        .replaceAll(RegExp(r'[xX]$'), '') // 뒤에 x 제거
        .trim();

    // 🔍 SPP 모드일 경우: 비정상적으로 붙는 '8888' 제거 (예: 8888801077384305 → 8801077384305)
    if (_scannerMode == "SPP") {
      if (cleaned.length > 13 && cleaned.startsWith("8888")) {
        cleaned = cleaned.substring(cleaned.length - 13);
        print("🔧 SPP 모드 프리픽스 제거 후: $cleaned");
      }
    }

    // 🔧 현재 스캐너 모드 출력
    print("🔧 현재 스캐너 모드: $_scannerMode");

    // ✅ HID + 갤럭시 폴드일 때만 보정 로직 적용
    if (_scannerMode == "HID" && isGalaxyFold()) {
      if (cleaned == "8") return "88";
      if (cleaned == "7") return "77";

      if (cleaned.startsWith("8") && !cleaned.startsWith("88")) {
        print("🔴 [보정 전] 바코드: $cleaned");
        cleaned = "88" + cleaned.substring(1);
        print("🟢 [보정 후] 바코드: $cleaned");
      } else if (cleaned.startsWith("7") && !cleaned.startsWith("77")) {
        print("🔴 [보정 전] 바코드: $cleaned");
        cleaned = "77" + cleaned.substring(1);
        print("🟢 [보정 후] 바코드: $cleaned");
      }
    }

    return cleaned;
  }



  // 바코드 카메라 스캔
  Future<String> _scanBarcodeCamera() async {

    try {
      final barcode = await Navigator.push(
        context,
        MaterialPageRoute(builder: (ctx) => const BarcodeScannerPage()),
      );

      if (!mounted) return "";

      if (barcode == null || barcode.isEmpty) {
        setState(() {
          _error = "바코드 스캔이 취소되었습니다.";
        });
        return ""; // ✅ 빈 문자열 반환 (예외 처리)
      } else {
        await _handleBarcode(barcode);
        return barcode; // ✅ 스캔된 바코드 값 반환
      }
    } catch (e) {
      setState(() {
        _error = "카메라 스캔 오류: $e";
      });
      return ""; // ✅ 오류 발생 시 빈 값 반환
    }
  }

  void _monitorConnection() {
    _bluetoothConnection?.input?.listen(null)?.onDone(() {
      print("❌ 블루투스 연결 끊김");
      setState(() {
        _isBluetoothConnected = false;
      });

      // 🔁 일정 시간 후 재시도 (or 버튼 눌러서 수동 시도도 가능하게)
      Future.delayed(Duration(seconds: 2), () {
        // _tryAutoReconnect();
      });
    });
  }


  /// 📌 HID 모드 (키보드 입력)
  void _onKey(RawKeyEvent event) {
    if (event is RawKeyDownEvent) {
      if (event.logicalKey == LogicalKeyboardKey.enter) {
        if (_barcodeBuffer.isNotEmpty) {
          _handleBarcode(_barcodeBuffer.trim());
          _barcodeBuffer = ""; // 버퍼 초기화
        }
      } else if (event.character != null && event.character!.isNotEmpty) {
        _barcodeBuffer += event.character!;
      }
    }
  }
  Set<String> _scannedBarcodes = {};

  void processBarcode(String raw) async {
    if (_scannerMode != "HID" || !isGalaxyFold()) {
      print("🚫 보정 비활성화 → 원본 사용");
      await _handleBarcode(raw.trim());
      return;
    }
    final cleaned = preprocessBarcode(raw);

    if (cleaned.isEmpty) return;

    await _handleBarcode(cleaned);
  }

  // 바코드 처리
  Future<void> _handleBarcode(String barcode) async {
    final authProvider = context.read<AuthProvider>();
    barcode = preprocessBarcode(barcode);

    if (barcode.isEmpty || _scannedBarcodes.contains(barcode)) {
      print("⛔️ 무시된 바코드: '$barcode'");
      return;
    }

    if (authProvider.user == null) {
      Navigator.pushReplacementNamed(context, '/login');
      return;
    }

    setState(() => _isLoading = true);

    try {
      final productProvider = context.read<ProductProvider>();

      if (productProvider.products.isEmpty) {
        Fluttertoast.showToast(msg: "상품 목록이 비어 있습니다.", gravity: ToastGravity.BOTTOM);
        return;
      }

      // ✅ 바코드 리스트 포함 여부로 상품 찾기
      final matchedProduct = productProvider.products.firstWhere(
            (p) {
          final barcodes = p['barcodes'] as List<dynamic>? ?? [];
          return barcodes.contains(barcode);
        },
        orElse: () => null,
      );

      if (matchedProduct == null) {
        Fluttertoast.showToast(msg: "조회된 상품이 없습니다.", gravity: ToastGravity.BOTTOM);
        return;
      }

      final product = matchedProduct;
      final productName = product['product_name'] ?? "상품명 없음";
      final defaultPrice = (product['default_price'] ?? 0).toDouble();
      final isProductFixedPrice = product['is_fixed_price'] == true;
      final clientRegularPrice = (widget.client['regular_price'] ?? 0).toDouble();
      final clientFixedPrice = (widget.client['fixed_price'] ?? 0).toDouble();
      final appliedPrice = isProductFixedPrice ? clientFixedPrice : clientRegularPrice;
      final priceType = isProductFixedPrice ? "고정가" : "일반가";

      if (_isReturnMode) {
        final existingIndex = _returnedItems.indexWhere((item) => item['product_id'] == product['id']);
        if (existingIndex >= 0) {
          setState(() {
            _returnedItems[existingIndex]['box_quantity']++;
          });
        } else {
          setState(() {
            _returnedItems.add({
              'product_id': product['id'],
              'name': productName,
              'box_quantity': 1,
              'box_count': 0,
              'default_price': defaultPrice,
              'client_price': appliedPrice,
              'price_type': priceType,
              'category': product['category'] ?? '',
            });
          });
        }
      } else {
        final existingIndex = _scannedItems.indexWhere((item) => item['product_id'] == product['id']);
        if (existingIndex >= 0) {
          setState(() {
            _scannedItems[existingIndex]['box_count']++;
          });
        } else {
          setState(() {
            _scannedItems.add({
              'product_id': product['id'],
              'name': productName,
              'box_quantity': product['box_quantity'] ?? 0,
              'box_count': 1,
              'default_price': defaultPrice,
              'client_price': appliedPrice,
              'price_type': priceType,
              'category': product['category'] ?? '',
            });
          });
        }
      }

      Fluttertoast.showToast(
        msg: "${_isReturnMode ? '반품' : '상품'} 추가됨: $productName",
        gravity: ToastGravity.BOTTOM,
      );
    } catch (e) {
      Fluttertoast.showToast(msg: "스캔 처리 오류: $e", gravity: ToastGravity.BOTTOM);
    } finally {
      setState(() => _isLoading = false);
    }
  }


//거래처정보테이블
  double get totalAmount {
    double sum = 0;
    for (var item in _scannedItems) {
      sum += (item['box_count'] * item['box_quantity'] * item['client_price']);
    }
    return sum;
  }
  Widget _buildClientInfoTable() {
    return GestureDetector(
      onTap: () {
        setState(() {
          _isClientInfoExpanded = !_isClientInfoExpanded;
        });
      },
      child: AnimatedContainer(
        duration: Duration(milliseconds: 250),
        padding: const EdgeInsets.all(8.0),
        decoration: BoxDecoration(
          color: Colors.grey.shade100, // 연한 배경색
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.indigo),
        ),
        child: Table(
          border: TableBorder.all(color: Colors.blueGrey.shade100),
          columnWidths: const {
            0: FractionColumnWidth(0.25),
            1: FractionColumnWidth(0.25),
            2: FractionColumnWidth(0.25),
            3: FractionColumnWidth(0.25),
          },
          children: [
            _buildTableRow("거래처명", widget.client['client_name'], "미수금",
                widget.client['outstanding_amount'].round()?.toString() ?? "0"),
            if (_isClientInfoExpanded)
              _buildTableRow("주소", widget.client['address'] ?? "정보 없음",
                  "전화번호", widget.client['phone'] ?? "정보 없음"),
            if (_isClientInfoExpanded)
              _buildTableRow("사업자 번호", widget.client['business_number'] ?? "정보 없음",
                  "이메일", widget.client['email'] ?? "정보 없음"),
            if (_isClientInfoExpanded)
              _buildTableRow("일반가", widget.client['regular_price'].round()?.toString() ?? "정보 없음",
                  "고정가", widget.client['fixed_price'].round()?.toString() ?? "정보 없음"),
          ],
        ),
      ),
    );
  }



  TableRow _buildTableRow(String title1, String value1, String title2, String value2) {
    return TableRow(children: [
      _buildTableCell(title1, isHeader: true),
      _buildTableCell(value1),
      _buildTableCell(title2, isHeader: true),
      _buildTableCell(value2),
    ]);
  }

  Widget _buildTableCell(String text, {bool isHeader = false}) {
    return Container(
      color: isHeader ? Colors.blueGrey.shade50 : null, // 제목 칸 연한 배경
      padding: const EdgeInsets.all(6.0),
      child: Text(
        text,
        style: TextStyle(
          fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
          fontSize: 12,
        ),
        overflow: TextOverflow.ellipsis,
      ),
    );
  }






  void _showPopup(String fullText) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("상세 정보"),
          content: Text(fullText),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("닫기"),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>(); // 인증 상태 가져오기

    if (authProvider.user == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.pushReplacementNamed(context, '/login');
      });
    }

    return Scaffold(
      // ✅ AppBar 완전 투명 + 상태바 유지
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        systemOverlayStyle: SystemUiOverlayStyle.dark,
        toolbarHeight: 0,
      ),

      body: Column(
        children: [
          _buildCustomAppBar(context), // ✅ 판매 화면 헤더 (배경색 유지)
          Expanded(
            child: RawKeyboardListener(
              focusNode: _keyboardFocusNode,
              autofocus: true,
              onKey: (RawKeyEvent event) {
                if (event is RawKeyDownEvent) {
                  if (event.logicalKey == LogicalKeyboardKey.power ||
                      event.logicalKey == LogicalKeyboardKey.select) {
                    print("⚠️ HID 스캐너 신호 감지됨 → 무시");
                    return;
                  }

                  if (event.logicalKey == LogicalKeyboardKey.enter) {
                    if (_barcodeBuffer.isNotEmpty) {
                      print("✅ 바코드 입력 완료: '$_barcodeBuffer'");
                      _handleBarcode(_barcodeBuffer.trim());
                      _barcodeBuffer = '';
                    }
                  } else if (event.character != null && event.character!.isNotEmpty) {
                    _barcodeBuffer += event.character!;
                  }
                }
              },

              // ✅ 롱프레스 초기화 기능 추가
              child: GestureDetector(
                onLongPress: _showClearConfirm,
                child: Column(
                  children: [
                    _buildClientInfoTable(), // 거래처 정보
                    Expanded(child: _buildScannedItemsTable()), // 스캔된 상품 목록
                    _buildSummaryRow(), // 합계

                    // ✅ 버튼 스타일 개선
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildModernButton("판매", Icons.shopping_cart, _isReturnMode ? Colors.grey.shade300 : Colors.blue, () {
                            setState(() => _isReturnMode = false);
                          }),
                          _buildModernButton("반품", Icons.replay, _isReturnMode ? Colors.red : Colors.grey.shade400, () {
                            setState(() => _isReturnMode = true);
                          }),
                          _buildModernButton("스캔", Icons.camera_alt, Colors.teal, _scanBarcodeCamera),
                          _buildModernButton("인쇄", Icons.print, Colors.indigo, _showPaymentDialog),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
  img.Image threshold(img.Image src, {int threshold = 160}) {
    final output = img.Image.from(src);
    for (int y = 0; y < output.height; y++) {
      for (int x = 0; x < output.width; x++) {
        final pixel = output.getPixel(x, y);
        final luma = img.getLuminance(pixel);
        if (luma < threshold) {
          output.setPixelRgba(x, y, 0, 0, 0, 255); // 검정
        } else {
          output.setPixelRgba(x, y, 255, 255, 255, 255); // 흰색
        }
      }
    }
    return output;
  }


  Future<void> _printReceiptImage(
      Map<String, dynamic> companyInfo, {
        required int todayPayment,
      }) async {
    final recorder = ui.PictureRecorder();
    const double width = 576;
    final canvas = Canvas(recorder);
    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(Rect.fromLTWH(0, 0, width, 1500), bgPaint);

    final textPainter = TextPainter(
      textDirection: widgets.TextDirection.ltr,
      maxLines: null,
    );

    final now = DateFormat("yyyy-MM-dd HH:mm:ss").format(DateTime.now());

    int totalBoxes = 0;
    int totalAmount = 0;

    String text = '''
[영수증]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
날짜: $now
${companyInfo['company_name']}  대표: ${companyInfo['ceo_name']}
${companyInfo['address']}
Tel: ${companyInfo['phone']}
사업자번호: ${companyInfo['business_number']}
────────────────────────────
거래처: ${widget.client['client_name']}
주소: ${widget.client['address']}
사업자번호: ${widget.client['business_number']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
상품명  박스수 단 가   유 형    합 계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
''';
    for (var item in _scannedItems) {
      int boxes = item['box_count'];
      int quantityPerBox = item['box_quantity'];
      double basePrice = (item['default_price'] ?? 0).toDouble();
      double clientRate = (item['client_price'] ?? 100).toDouble();
      String priceType = item['price_type'] ?? '일반가';

      int unitPrice = (basePrice * clientRate * 0.01 * quantityPerBox).round(); // ✅ 박스 수량 반영
      int total = boxes * unitPrice;

      totalBoxes += boxes;
      totalAmount += total;

      text +=
          '${item['name'].padRight(4)}' +
              '${boxes.toString().padLeft(4)}' +
              '${unitPrice.toString().padLeft(7)}' +
              '  ${priceType.padRight(0)}  ' +
              '${formatter.format(total).padLeft(3)}원\n';
    }


    for (var item in _returnedItems) {
      int boxes = item['box_count'];
      double basePrice = (item['default_price'] ?? 0).toDouble();
      double clientRate = (item['client_price'] ?? 100).toDouble();
      String priceType = item['price_type'] ?? '일반가';

      int unitPrice = (basePrice * clientRate * 0.01).round();
      int total = (item['box_quantity'] * boxes * unitPrice * -1);

      totalBoxes += boxes;
      totalAmount += total;

      text +=
          '${item['name'].padRight(3)}' +
              '${boxes.toString().padLeft(5)}' +
              '${unitPrice.toString().padLeft(6)}' +
              '  ${priceType.padRight(4)}  ' +
              '${formatter.format(total).padLeft(9)}원\n';
    }



// ✔ 총합 및 입금/미수금
    final double rawOutstanding = widget.client['outstanding_amount']?.toDouble() ?? 0.0;
    final double finalOutstanding = rawOutstanding - todayPayment;

    text += '''
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
박스수: ${totalBoxes.toString().padLeft(0)}     
총금액: ${formatter.format(totalAmount).padLeft(0)} 원
전잔액: ${formatter.format(widget.client['outstanding_amount']).padLeft(0)} 원
입 금: ${formatter.format(todayPayment).padLeft(0)} 원
미수금: ${formatter.format(finalOutstanding.round()).padLeft(0)} 원
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
담당자: ${context.read<AuthProvider>().user?.name ?? ''}   H.P: ${context.read<AuthProvider>().user?.phone ?? ''}
입금계좌: ${companyInfo['bank_account']}
''';

    textPainter.text = TextSpan(
      text: text,
      style: TextStyle(
        color: Colors.black,
        fontSize: 28,
        fontFamily: 'Courier', // 고정폭 글꼴로 정렬 개선
      ),
    );

    textPainter.layout(maxWidth: width - 20);
    textPainter.paint(canvas, const Offset(10, 10));

    final picture = recorder.endRecording();
    final lineCount = '\n'.allMatches(text).length + 5;
    final height = (lineCount * 34).clamp(600, 1800).toDouble();
    final image = await picture.toImage(width.toInt(), height.toInt());


    final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final pngBytes = byteData!.buffer.asUint8List();

    final decodedImage = img.decodeImage(pngBytes);
    if (decodedImage == null) {
      Fluttertoast.showToast(msg: "❌ 이미지 디코딩 실패");
      return;
    }

    final gray = img.grayscale(decodedImage);
    final bwImage = threshold(gray, threshold: 160);

    final profile = await CapabilityProfile.load();
    final generator = Generator(PaperSize.mm80, profile);
    final ticket = <int>[];
    ticket.addAll(generator.image(bwImage));
    ticket.addAll(generator.feed(2));
    ticket.addAll(generator.cut());

    final writeChar = await _getConnectedPrinterWriteCharacteristic();
    if (writeChar == null) {
      Fluttertoast.showToast(msg: "⚠️ 프린터 연결 안 됨");
      return;
    }

    const chunkSize = 200;
    for (int i = 0; i < ticket.length; i += chunkSize) {
      final end = (i + chunkSize < ticket.length) ? i + chunkSize : ticket.length;
      await writeChar.write(
        ticket.sublist(i, end),
        withoutResponse: false,
      );
      await Future.delayed(const Duration(milliseconds: 10));
    }

    Fluttertoast.showToast(msg: "✅ 한글 영수증 인쇄 완료");
  }

  Future<void> _sendSms(String phoneNumber) async {
    final Uri uri = Uri.parse('sms:$phoneNumber');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      Fluttertoast.showToast(msg: "문자 앱을 열 수 없습니다.");
    }
  }

  /// 📌 헤더 스타일 조정
  Widget _buildCustomAppBar(BuildContext context) {
    final printerProvider = context.watch<BluetoothPrinterProvider>();
    final isPrinterConnected = printerProvider.isConnected;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.indigo, // ✅ 전체 배경색 적용
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 6,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // ✅ 왼쪽: 홈 버튼 추가 (HomeScreen으로 이동)
          GestureDetector(
            onTap: () {
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(
                  builder: (context) => HomeScreen(token: widget.token), // 🔹 `token` 전달 추가
                ),
                    (route) => false, // 🔹 뒤로 가기 스택 삭제 (홈 화면이 최상위 화면이 됨)
              );
            },
            child: Row(
              children: [
                Icon(Icons.home_rounded, color: Colors.white, size: 22),
                SizedBox(width: 6),
                Text(
                  "홈",
                  style: TextStyle(fontSize: 16, color: Colors.white),
                ),
              ],
            ),
          ),

          // ✅ 중앙: "판매 화면"
          Expanded(
            child: Center(
              child: GestureDetector(
                onTap: () {
                  final phone = widget.client['phone'];
                  if (phone != null && phone.toString().isNotEmpty) {
                    _sendSms(phone);
                  } else {
                    Fluttertoast.showToast(msg: "전화번호가 없습니다.");
                  }
                },
                child: const Text(
                  "     판   매",
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),

          GestureDetector(
            onTap: _showBluetoothPrinterDialog,  // 누르면 연결 팝업
            child: Row(
              children: [
                Icon(
                  _isPrinterConnected ? Icons.bluetooth_connected : Icons.bluetooth_disabled,
                  color: _isPrinterConnected ? Colors.lightGreen : Colors.redAccent,
                ),
                SizedBox(width: 6),
                Text(
                  _isPrinterConnected ? "프린터" : "프린터",
                  style: TextStyle(color: Colors.white, fontSize: 12),
                ),
              ],
            ),
          ),
          // ✅ 오른쪽: 연결 상태 (클릭 가능)
          GestureDetector(
            onTap: _showBluetoothDialog,
            child: Row(
              children: [
                Icon(
                  _isBluetoothConnected ? Icons.bluetooth_connected : Icons.bluetooth_disabled,
                  color: _isBluetoothConnected ? Colors.lightGreenAccent : Colors.redAccent,
                  size: 20,
                ),
                SizedBox(width: 4),
                Text(
                  _isBluetoothConnected ? "스캐너" : "스캐너",
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.white,
                    decoration: TextDecoration.underline, // 👈 클릭 강조 느낌
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }








  Widget _buildModernButton(String label, IconData icon, Color color, VoidCallback onPressed) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: EdgeInsets.symmetric(vertical: 14, horizontal: 20),
        elevation: 2, // ✅ 버튼 그림자 추가
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: Colors.white, size: 22),
          SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(fontSize: 14, color: Colors.white, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }


  void _showClearConfirm() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("판매 목록 초기화"),
        content: Text("판매 및 반품 목록을 정말로 초기화할까요?"),
        actions: [
          TextButton(
            child: Text("취소"),
            onPressed: () => Navigator.of(context).pop(),
          ),
          ElevatedButton(
            child: Text("초기화"),
            onPressed: () {
              Navigator.of(context).pop();
              _clearAllItems();
            },
          ),
        ],
      ),
    );
  }


  void _showBluetoothDialog() async {
    List<spp.BluetoothDevice> devices = await spp.FlutterBluetoothSerial.instance.getBondedDevices();
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("블루투스 장치 연결"),
          content: SingleChildScrollView(
            child: Column(
              children: devices.map((device) {
                return ListTile(
                  title: Text(device.name ?? "이름 없음"),
                  subtitle: Text(device.address),
                  onTap: () {
                    Navigator.pop(context);
                    _connectToDevice(device);
                  },
                );
              }).toList(),
            ),
          ),
          actions: [
            TextButton(
              child: Text("최근 기기 다시 연결"),
              onPressed: () {
                Navigator.pop(context);
                // _tryAutoReconnect();
              },
            ),
            TextButton(
              child: Text("닫기"),
              onPressed: () {
                Navigator.pop(context);
              },
            ),
          ],
        );
      },
    );

  }
  // Future<void> _tryAutoReconnect() async {
  //   final prefs = await SharedPreferences.getInstance();
  //   final address = prefs.getString('last_device_address');
  //
  //   if (address != null) {
  //     try {
  //       final connection = await spp.BluetoothConnection.toAddress(address);
  //       setState(() => _bluetoothConnection = connection);
  //       Fluttertoast.showToast(msg: "이전 장치 자동 연결됨");
  //     } catch (e) {
  //       print("자동 연결 실패: $e");
  //     }
  //   }
  // }

  Future<void> _connectToDevice(spp.BluetoothDevice device) async {
    if (_isConnecting) return;
    _isConnecting = true;

    try {
      // 이전 연결 정리
      if (_bluetoothConnection != null) {
        await _bluetoothConnection!.finish();
        _bluetoothConnection = null;
      }

      if (_inputSubscription != null) {
        await _inputSubscription!.cancel();
        _inputSubscription = null;
      }

      print("🔌 연결 시도 중: ${device.name}");

      final connection = await spp.BluetoothConnection.toAddress(device.address);
      _bluetoothConnection = connection;

      _inputSubscription = connection.input?.listen(
            (data) {
          final raw = String.fromCharCodes(data);
          print("📦 바코드 수신: '$raw'");
          processBarcode(raw);
        },
        onDone: () {
          print("❌ 연결 끊김");
          setState(() => _isBluetoothConnected = false);
        },
        onError: (e) {
          print("⚠️ 수신 에러: $e");
        },
        cancelOnError: true,
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('last_device_address', device.address);

      setState(() {
        _isBluetoothConnected = true;
        _isPrinterConnected = true;
        _connectedDeviceName = device.name;
      });

      Fluttertoast.showToast(msg: "${device.name} 연결 성공");
    } catch (e) {
      print("❌ 연결 실패: $e");
      Fluttertoast.showToast(msg: "연결 실패: $e");
    } finally {
      _isConnecting = false;
    }
  }


  void _scanReturnItems() async {
    _isReturnMode = true; // ✅ 반품 모드 활성화
    // ✅ 카메라 스캔 실행 후 바코드 값 가져오기
    String scannedBarcode = await _scanBarcodeCamera();

    if (scannedBarcode.isNotEmpty) {
      var product = _findProductByBarcode(scannedBarcode);

      if (product != null) {
        setState(() {
          bool isFixedPrice = widget.client['price_type'] == true;
          double unitPrice = isFixedPrice
              ? (product['fixed_price'] ?? 0) * 0.01
              : (product['regular_price'] ?? 0) * 0.01;

          _returnedItems.add({
            'name': product['name'],
            'barcode': scannedBarcode,
            'quantity': 1, // ✅ 바코드 찍는 숫자 (낱개)
            'unit_price': unitPrice, // ✅ 단가 (일반가 or 고정가)
            'total_price': -unitPrice, // ✅ 반품 금액 (빨간색, 마이너스 값)
          });
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("상품을 찾을 수 없습니다.")),
        );
        _isReturnMode = false; // ✅ 반품 모드 종료
      }
    }
  }


  void _showPaymentDialog() {
    double outstandingAmount = widget.client['outstanding_amount']?.toDouble() ?? 0;
    TextEditingController paymentController = TextEditingController(text: "");
    bool isSubsidy = false; // ✅ 지원금 체크박스 상태 변수 추가

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder( // ✅ 팝업 내부에서도 상태 업데이트 가능하도록 함
          builder: (context, setState) {
            return AlertDialog(
              title: Text("입금 / 지원금 처리"),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text("현재 미수금: ${outstandingAmount.toStringAsFixed(2)} 원"),
                  SizedBox(height: 10),
                  TextField(
                    controller: paymentController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: "입금 금액 입력 (빈 값은 0 처리)",
                      border: OutlineInputBorder(),
                    ),
                  ),
                  SizedBox(height: 10),
                  Row(
                    children: [
                      Checkbox(
                        value: isSubsidy,
                        onChanged: (value) {
                          setState(() {
                            isSubsidy = value ?? false;
                          });
                        },
                      ),
                      Text("이 금액을 지원금으로 처리"),
                    ],
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text("취소"),
                ),
                ElevatedButton(
                  onPressed: () {
                    double amount = double.tryParse(paymentController.text.trim()) ?? 0;

                    if (isSubsidy) {
                      _applySubsidy(amount); // ✅ 지원금으로 처리
                    } else {
                      _processPayment(amount); // ✅ 일반 입금 처리

                    }

                    Navigator.of(context).pop(); // 팝업 닫기
                  },
                  child: Text("확인"),
                ),
              ],
            );
          },
        );
      },
    );
  }
  void _applySubsidy(double subsidyAmount) async {
    final auth = context.read<AuthProvider>();
    final clientId = widget.client['id'];
    final String nowStr = DateTime.now().toIso8601String();

    final payload = {
      "employee_id": auth.user?.id,
      "client_id": clientId,
      "product_id": null,  // ✅ 제품 없음
      "quantity": 0,       // ✅ 수량 0
      "sale_datetime": nowStr,
      "return_amount": 0,
      "subsidy_amount": subsidyAmount,  // ✅ 지원금 전송
    };

    final resp = await ApiService.createSales(widget.token, payload);
    if (resp.statusCode == 200 || resp.statusCode == 201) {
      Fluttertoast.showToast(msg: "지원금이 적용되었습니다.");
    } else {
      Fluttertoast.showToast(msg: "지원금 적용 실패: ${resp.body}");
    }
  }

  Future<Map<String, dynamic>?> _fetchCompanyInfo() async {
    final data = await ApiService.fetchCompanyInfo(widget.token);
    if (data == null) {
      Fluttertoast.showToast(msg: "회사 정보를 불러올 수 없습니다.");
    }
    return data;
  }



  //미수금 차감 및 서버 전송
  void _processPayment(double paymentAmount) async {
    final int clientId = widget.client['id'];
    final String nowStr = DateTime.now().toIso8601String();
    final auth = context.read<AuthProvider>();

    if (paymentAmount < 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("입금 금액은 0 이상이어야 합니다.")),
      );
      return;
    }

    try {
      // ✅ 미수금 = 기존 미수금 + 스캔한 상품 가격 - 입금액
      double updatedOutstandingAmount = widget.client['outstanding_amount'] + totalScannedItemsPrice - paymentAmount;

      // ✅ UI 업데이트
      setState(() {
        widget.client['outstanding_amount'] = updatedOutstandingAmount; // ✅ 위젯 값 변경
        client['outstanding_amount'] = updatedOutstandingAmount; // ✅ 상태 값 변경
      });

      // ✅ 서버 업데이트
      final response = await ApiService.updateClientOutstanding(
        widget.token,
        widget.client['id'],
        {"outstanding_amount": updatedOutstandingAmount},
      );
      for (var item in _scannedItems) {
        final int totalUnits = item['box_count'];
        final double returnAmount = 0.0; // ✅ 기본적으로 반품 금액 0으로 설정
        final payload = {
          "employee_id": auth.user?.id, // ✅ 직원 ID 포함
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": totalUnits,
          "sale_datetime": nowStr,
          "return_amount": returnAmount,
        };

        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("매출 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }
      // ✅ 반품 상품 서버 전송
      for (var item in _returnedItems) {
        final int totalUnits = item['box_quantity'];
        final double defaultPrice = (item['default_price'] ?? 0).toDouble();
        final double clientPrice = (item['client_price'] ?? 0).toDouble();
        final double returnAmount = (totalUnits * defaultPrice * clientPrice * 0.01).toDouble();
        developer.log ("전송 : $totalUnits , $item['default_price'] , $item['client_price'] ");
        final payload = {
          "employee_id": auth.user?.id,
          "client_id": clientId,
          "product_id": item['product_id'],
          "quantity": -totalUnits, // ✅ 반품은 음수로 처리
          "sale_datetime": nowStr,
          "return_amount": returnAmount, // ✅ 반품 금액 추가
        };
        developer.log("📡 반품 데이터 전송: $payload");  // ✅ API 요청 전에 확인
        final resp = await ApiService.createSales(widget.token, payload);
        if (resp.statusCode != 200 && resp.statusCode != 201) {
          throw Exception("반품 등록 실패: ${resp.statusCode} / ${resp.body}");
        }
      }


      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("입금이 성공적으로 처리되었습니다.")),
        );
        final companyInfo = await _fetchCompanyInfo(); // ✅ 회사 정보 가져오기
        if (companyInfo != null) {
          if (_printerLanguage == 'non-korean') {
            if (_printerPaperSize == '55mm') {
              await _printReceiptImage55mm(companyInfo);
            } else {
              final int safePaymentAmount = paymentAmount.toInt(); // double → int

              await _printReceiptImage(
                companyInfo,
                todayPayment: safePaymentAmount,
              );
            }
          } else {
            if (_printerPaperSize == '55mm') {
              _printKoreanText_55mm(companyInfo); //  55mm 한글지원
            } else {
              _printKoreanText_80mm(companyInfo); //  80mm 한글지원
            }
          }
        }
        setState(() {
          _scannedItems = List.from([]); // ✅ 스캔한 상품 목록 초기화
          _returnedItems.clear();
        });

      } else {
        throw Exception("서버 오류: ${response.body}");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("입금 처리 중 오류 발생: $e")),
      );
    }
  }

  Future<void> _printReceiptImage55mm(Map<String, dynamic> companyInfo) async {
    // 1️⃣ canvas 크기 조정 (55mm 용지 폭 기준)
    final recorder = ui.PictureRecorder();
    const double width = 384; // 보통 55mm 프린터는 약 384px
    final canvas = Canvas(recorder);
    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(Rect.fromLTWH(0, 0, width, 800), bgPaint);

    final textPainter = TextPainter(
      textDirection: widgets.TextDirection.ltr,
      maxLines: null,
    );

    final now = DateFormat("yyyy-MM-dd HH:mm:ss").format(DateTime.now());

    String text = '''
[영수증]
날짜: $now

${companyInfo['company_name']}
${companyInfo['address']}
Tel: ${companyInfo['phone']}
사업자: ${companyInfo['business_number']}

거래처: ${widget.client['client_name']}
미수금: ${formatter.format(widget.client['outstanding_amount'])} 원

----------------------
''';

    for (var item in _scannedItems) {
      int total = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price'] * 0.01).round();
      text += "${item['name']} x${item['box_count']} - ${formatter.format(total)}원\n";
    }

    for (var item in _returnedItems) {
      double total = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price']) * -0.01;
      text += "[반품] ${item['name']} x${item['box_count']} - ${formatter.format(total.round())}원\n";
    }

    text += '''
----------------------
입금계좌: ${companyInfo['bank_account']}
''';

    textPainter.text = TextSpan(
      text: text,
      style: TextStyle(color: Colors.black, fontSize: 16),
    );

    textPainter.layout(maxWidth: width - 20);
    textPainter.paint(canvas, Offset(10, 10));

    final picture = recorder.endRecording();
    final ui.Image image = await picture.toImage(width.toInt(), 800);
    final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
    final pngBytes = byteData!.buffer.asUint8List();

    final decodedImage = img.decodeImage(pngBytes);
    if (decodedImage == null) {
      Fluttertoast.showToast(msg: "❌ 이미지 디코딩 실패");
      return;
    }

    final profile = await CapabilityProfile.load();
    final generator = Generator(PaperSize.mm58, profile); // ✅ 58mm → 55mm 대체
    final ticket = <int>[];
    ticket.addAll(generator.image(decodedImage));
    ticket.addAll(generator.feed(2));
    ticket.addAll(generator.cut());

    final writeChar = await _getConnectedPrinterWriteCharacteristic();
    if (writeChar == null) {
      Fluttertoast.showToast(msg: "⚠️ 프린터 연결 안 됨");
      return;
    }

    const chunkSize = 200;
    for (int i = 0; i < ticket.length; i += chunkSize) {
      int end = (i + chunkSize < ticket.length) ? i + chunkSize : ticket.length;
      await writeChar.write(ticket.sublist(i, end), withoutResponse: false);
      await Future.delayed(Duration(milliseconds: 10));
    }

    Fluttertoast.showToast(msg: "✅ 55mm 한글미지원 인쇄 완료");
  }


  void _printKoreanText_80mm(Map<String, dynamic> companyInfo) async {
    final buffer = StringBuffer();
    final now = DateFormat("yyyy-MM-dd HH:mm:ss").format(DateTime.now());

    buffer.writeln("영수증 (80mm)");
    buffer.writeln("일시: $now");
    buffer.writeln("회사: ${companyInfo['company_name']}");
    buffer.writeln("주소: ${companyInfo['address']}");
    buffer.writeln("거래처: ${widget.client['client_name']}");
    buffer.writeln("------------------------------");

    for (var item in _scannedItems) {
      int total = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price'] * 0.01).round();
      buffer.writeln("${item['name']} x${item['box_count']} = ${formatter.format(total)}원");
    }

    buffer.writeln("------------------------------");
    buffer.writeln("총 금액: ${formatter.format(totalScannedItemsPrice)}원");

    final writeChar = await _getConnectedPrinterWriteCharacteristic();
    if (writeChar == null) return;

    List<int> bytes = utf8.encode(buffer.toString());
    for (int i = 0; i < bytes.length; i += 180) {
      int end = (i + 180 < bytes.length) ? i + 180 : bytes.length;
      await writeChar.write(bytes.sublist(i, end));
      await Future.delayed(Duration(milliseconds: 50));
    }

    Fluttertoast.showToast(msg: "✅ 80mm 한글 인쇄 완료");
  }
  void _printKoreanText_55mm(Map<String, dynamic> companyInfo) async {
    final buffer = StringBuffer();
    final now = DateFormat("MM/dd HH:mm").format(DateTime.now());

    buffer.writeln("▶ 55mm 영수증 ◀");
    buffer.writeln("[$now]");
    buffer.writeln("${widget.client['client_name']}");

    for (var item in _scannedItems) {
      int total = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price'] * 0.01).round();
      buffer.writeln("${item['name'].substring(0, 6)} ${item['box_count']}개 ${formatter.format(total)}");
    }

    buffer.writeln("총액: ${formatter.format(totalScannedItemsPrice)}원");

    final writeChar = await _getConnectedPrinterWriteCharacteristic();
    if (writeChar == null) return;

    List<int> bytes = utf8.encode(buffer.toString());
    for (int i = 0; i < bytes.length; i += 180) {
      int end = (i + 180 < bytes.length) ? i + 180 : bytes.length;
      await writeChar.write(bytes.sublist(i, end));
      await Future.delayed(Duration(milliseconds: 50));
    }

    Fluttertoast.showToast(msg: "✅ 55mm 한글 인쇄 완료");
  }

  Widget _buildScannedItemsTable() {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade400),
        borderRadius: BorderRadius.circular(8),
        color: Colors.white,
      ),
      child: Column(
        children: [
          // ✅ 고정된 헤더 (배경색 추가)
          Container(
            height: 35,
            color: Colors.black45,
            child: _buildHeaderRow(),
          ),

          // ✅ 상품 목록 (판매 + 반품)
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.vertical,
              child: Column(
                children: [
                  _buildDataRows(),  // ✅ 판매 상품 리스트
                  _buildReturnRows(), // ✅ 반품 상품 리스트 (같은 구조)
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildReturnRows() {
    return Column(
      children: List.generate(_returnedItems.length, (index) {
        var item = _returnedItems[index];

        // ✅ 반품 합계 금액 정상 계산 (4열 포함)
        double totalPrice = (item['box_quantity'] * item['default_price'] * item['client_price'] * 0.01) * -1;


        return Container(
          decoration: BoxDecoration(
            color: Colors.red.shade50, // ✅ 반품 상품 배경색 (연한 빨간색)
            border: Border(bottom: BorderSide(color: Colors.red.shade300, width: 0.5)), // ✅ 반품 테이블 구분선
          ),
          padding: EdgeInsets.symmetric(vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildDataCell(item['name'].toString(), isRed: true),
              // 박스수량
              _buildDataCell(item['box_quantity'].toString(), isRed: true),
              // 개수
              _buildDataCell(item['box_count'].toString(), isRed: true),
              // 원래상품가격
              _buildDataCell(formatter.format(item['default_price'].toInt()), isRed: true),
              // 거래처 단가
              _buildDataCell(formatter.format(item['client_price'].toInt()), isRed: true),
              // 가격유형
              _buildDataCell(item['price_type'], isRed: true),
              // 합계(음수)
              _buildDataCell(formatter.format(totalPrice.toInt()), isBold: true, isRed: true),
            ],
          ),
        );
      }),
    );
  }



  Widget _buildHeaderRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _buildHeaderCell("상품명"),
        _buildHeaderCell("개수"),
        _buildHeaderCell("박스수"),
        _buildHeaderCell("가격"),
        _buildHeaderCell("단가"),
        _buildHeaderCell("유형"),
        _buildHeaderCell("합계"),
      ],
    );
  }


  List<DataColumn> _buildColumns() {
    return [
      DataColumn(label: _buildHeaderCell('상품명')),
      DataColumn(label: _buildHeaderCell('개수')),
      DataColumn(label: _buildHeaderCell('박스수')),
      DataColumn(label: _buildHeaderCell('가격')),
      DataColumn(label: _buildHeaderCell('단가')),
      DataColumn(label: _buildHeaderCell('유형')),
      DataColumn(
        label: SizedBox(
          width: 120, // ✅ 합계 열을 더 크게 설정
          child: _buildHeaderCell('합계'),
        ),
      ),
    ];
  }

  Widget _buildHeaderCell(String text) {
    return Expanded(
      child: Container(
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(vertical: 6),
        child: Text(
          text,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Colors.white, // ✅ 헤더 텍스트 색상
          ),
        ),
      ),
    );
  }
  // 상품 목록 테이블을 렌더링
  Widget _buildDataRows() {
    return Column(
      children: List.generate(_scannedItems.length, (index) {
        var item = _scannedItems[index];

        // ✅ 상품 자체의 가격 유형 확인 (is_fixed_price 사용)
        bool isFixedPrice = item['price_type'] == "고정가";


        // ✅ 총 가격 = (박스수량 * 개수 * 단가)
        int totalPrice = (item['box_quantity'] * item['box_count'] * item['default_price'] * item['client_price']* 0.01).round();

        return GestureDetector(
          onTap: () {
            _selectItem(index);
            _showEditQuantityDialog(index);
          },  // 클릭 시 해당 상품 선택
          child: Container(
            decoration: BoxDecoration(
              color: index == selectedIndex ? Colors.blue.shade100 : (index.isEven ? Colors.grey.shade100 : Colors.white), // 선택된 행 색상 변경
              border: Border(
                bottom: BorderSide(color: Colors.grey.shade300, width: 0.5), // 가로줄 스타일
              ),
            ),
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildDataCell(item['name'].toString()), // 상품명
                _buildDataCell(item['box_quantity'].toString()), // 박스 수량
                _buildDataCell(item['box_count'].toString()), // 수량
                _buildDataCell(formatter.format(item['default_price'].round())), // ✅ 상품 원래 가격
                _buildDataCell(formatter.format(item['client_price'].toInt())), // ✅ 거래처 단가
                _buildDataCell(isFixedPrice ? '고정가' : '일반가'), // ✅ 가격 유형
                _buildDataCell(formatter.format(totalPrice), isBold: true), // ✅ 합계
              ],
            ),
          ),
        );
      }),
    );
  }






  DataRow _buildEmptyDataRow() {
    return DataRow(
      cells: List.generate(
        7,
            (index) => DataCell(
          Center(
            child: Text(
              "-",
              style: TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDataCell(String text, {bool isBold = false, bool isRed = false}) {
    return Expanded(
      child: Center(
        child: Text(
          text,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal, // ✅ 합계는 볼드 처리
            color: isRed ? Colors.red : Colors.black87,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }


  Widget _buildSummaryRow() {
    final formatter = NumberFormat("#,###"); // ✅ 천단위 콤마 적용

    // ✅ 판매 상품의 총 박스수량 계산
    int totalBoxCount = _scannedItems.fold(0, (sum, item) {
      int boxQty = (item['box_quantity'] ?? 0).toInt();
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum + (boxQty * boxCnt);
    });

    // ✅ 반품 상품의 총 박스수량 계산 (음수로 적용)
    int totalReturnBoxCount = _returnedItems.fold(0, (sum, item) {
      int boxQty = (item['box_quantity'] ?? 0).toInt();
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum - (boxQty);
    });

    // ✅ 판매 상품의 총 수량 계산
    int totalItemCount = _scannedItems.fold(0, (sum, item) {
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum + boxCnt;
    });

    // ✅ 반품 상품의 총 수량 계산 (음수로 적용)
    int totalReturnItemCount = _returnedItems.fold(0, (sum, item) {
      int boxCnt = (item['box_count'] ?? 0).toInt();
      return sum - boxCnt;
    });

    // ✅ 판매 상품의 총 판매 금액 계산 (상품 가격 * 거래처 단가 포함)
    int totalSalesAmount = _scannedItems.fold(0, (sum, item) {
      int boxQuantity = (item['box_quantity'] ?? 0);
      int boxCount = (item['box_count'] ?? 0);
      double defaultPrice = item['default_price'] ?? 0.0;
      double clientPrice = item['client_price'] ?? 0.0;

      return sum + ((boxQuantity * boxCount * defaultPrice * clientPrice) * 0.01).round();
    });

    // ✅ 반품 상품의 총 반품 금액 계산 (상품 가격 * 거래처 단가 포함, 음수 적용)
    int totalReturnAmount = _returnedItems.fold(0, (sum, item) {
      int boxQuantity = (item['box_quantity'] ?? 0);
      int boxCount = (item['box_count'] ?? 0);
      double defaultPrice = item['default_price'] ?? 0.0;
      double clientPrice = item['client_price'] ?? 0.0;

      return sum - ((boxQuantity * defaultPrice * clientPrice) * 0.01).round();
    });
    totalReturnedItemsPrice = -totalReturnAmount.toDouble();
    // ✅ 최종 총 매출 금액 계산 (판매 - 반품)
    int finalTotal = totalSalesAmount + totalReturnAmount;
    totalScannedItemsPrice = finalTotal.toDouble();
    return Container(
      padding: EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      margin: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFFEEEEEE), Color(0xFFD6D6D6)], // ✅ 세련된 연한 그라디언트 적용
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16), // ✅ 둥근 모서리
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 6,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildSummaryCell("📦 박스수", formatter.format(totalItemCount), textColor: Colors.blue.shade700),
          _buildSummaryCell("🔄 반품", formatter.format(totalReturnedItemsPrice), isRed: true),
          _buildSummaryCell("💰 총 금액", formatter.format(totalScannedItemsPrice) + " 원", isBold: true, textColor: Colors.green.shade800),
        ],
      ),
    );
  }


  // ✅ 바코드로 상품 찾기 함수 추가
  Map<String, dynamic>? _findProductByBarcode(String barcode) {
    return _scannedItems.firstWhere(
          (product) => product['barcode'] == barcode,
      orElse: () => <String, dynamic>{}, // ✅ 빈 맵 반환하여 null 방지
    );
  }




  /// 📌 합계 데이터 셀 (아이콘 추가)
  Widget _buildSummaryCell(String label, String value, {bool isBold = false, bool isRed = false, Color textColor = Colors.black}) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: Colors.grey.shade700, // ✅ 라벨 색상 고정 (연한 회색)
            ),
          ),
          SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: isRed ? Colors.red : textColor, // ✅ 기본 색상 적용
            ),
          ),
        ],
      ),
    );
  }


  //거래처 정보 갱신
  void _fetchUpdatedClientInfo() async {
    try {
      final response = await ApiService.fetchClientById(widget.token, client['id']);
      if (response.statusCode == 200) {
        var updatedClient = jsonDecode(response.body) as Map<String, dynamic>;

        setState(() {
          client = updatedClient; // ✅ 새로운 Map으로 복사하여 UI 강제 갱신
        });
      } else {
        throw Exception("거래처 정보 갱신 실패");
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("거래처 정보 업데이트 실패: $e")),
      );
    }
  }
  // 수량 수정 다이얼로그
  // 수량 수정 다이얼로그
  void _showEditQuantityDialog(int index) {
    TextEditingController quantityController = TextEditingController(
      text: _scannedItems[index]['box_count'].toString(),
    );

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text("수량 수정"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // 수량 감소 버튼
                  IconButton(
                    icon: Icon(Icons.remove),
                    onPressed: () {
                      int currentQty = int.tryParse(quantityController.text) ?? 0;
                      setState(() {
                        quantityController.text = (currentQty - 1).toString(); // ✅ 음수도 허용
                      });
                    },
                  ),
                  // 수량 입력 필드 (음수 허용)
                  Expanded(
                    child: TextField(
                      controller: quantityController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(labelText: "수량 입력"),
                    ),
                  ),
                  // 수량 증가 버튼
                  IconButton(
                    icon: Icon(Icons.add),
                    onPressed: () {
                      int currentQty = int.tryParse(quantityController.text) ?? 0;
                      setState(() {
                        quantityController.text = (currentQty + 1).toString();
                      });
                    },
                  ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                int newQuantity = int.tryParse(quantityController.text) ?? 0;

                if (newQuantity == 0) {
                  // ✅ 0일 경우 삭제, 팝업이 닫힌 후 삭제 실행
                  Navigator.of(context).pop(); // 팝업 닫기
                  Future.delayed(Duration(milliseconds: 200), () {
                    _deleteItem(index); // 삭제 실행
                  });
                } else {
                  // ✅ 0이 아닐 경우 업데이트
                  setState(() {
                    _scannedItems[index]['box_count'] = newQuantity;
                  });
                  Navigator.of(context).pop(); // 팝업 닫기
                }
              },
              child: Text("확인"),
            ),
          ],
        );
      },
    );
  }


// 스캔한 상품 삭제
  void _deleteItem(int index) {
    setState(() {
      _scannedItems.removeAt(index); // 해당 인덱스의 상품 삭제
    });
  }


  void _clearAllItems() {
    setState(() {
      _scannedItems.clear(); // 모든 상품 목록 초기화
      _returnedItems.clear(); // ✅ 모든 반품 목록 초기화
    });
    Fluttertoast.showToast(msg: "판매 및 반품 목록이 초기화되었습니다.", gravity: ToastGravity.BOTTOM);
  }


}
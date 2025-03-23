import 'package:flutter/material.dart';
import '../services/sales_service.dart';
import 'dart:convert'; // ✅ UTF-8 디코딩을 위해 필요
import '../config.dart';
import '../screens/home_screen.dart';

final String baseUrl = BASE_URL;


class SalesSummaryScreen extends StatefulWidget {
  final String token;
  final int employeeId;

  SalesSummaryScreen({required this.token, required this.employeeId});

  @override
  _SalesSummaryScreenState createState() => _SalesSummaryScreenState();
}

class _SalesSummaryScreenState extends State<SalesSummaryScreen> {
  String selectedType = "일매출";
  DateTime selectedDate = DateTime.now();
  final SalesService salesService = SalesService("$baseUrl");

  Future<List<dynamic>>? salesData;
  Map<String, dynamic> outstandingMap = {}; // ✅ 미수금 저장할 Map 추가

  @override
  void initState() {
    super.initState();
    _fetchSalesData();
  }

  void _fetchSalesData() {
    setState(() {
      if (selectedType == "일매출") {
        salesData = salesService.fetchDailySales(
          widget.token,
          widget.employeeId,
          selectedDate.toString().split(' ')[0],
        ).then((data) {
          print("📌 Received Daily Sales Data: $data");
          return _processDailySales(data);
        });
      } else if (selectedType == "월매출") {
        salesData = salesService.fetchMonthlySales(
            widget.token, widget.employeeId, selectedDate.year, selectedDate.month
        ).then((data) {
          print("📌 Received Monthly Sales Data: $data");
          return _processMonthlySales(data);
        });
      } else {
        salesData = salesService.fetchYearlySales(
            widget.token, widget.employeeId, selectedDate.year
        ).then((data) {
          print("📌 Received Yearly Sales Data: $data");
          return _processYearlySales(data);
        });
      }
    });
  }
  Future<List<Map<String, dynamic>>> _processDailySales(List<dynamic> salesData) async {
    await _fetchOutstandingData();
    var allClients = await salesService.fetchAllClients(widget.token, widget.employeeId);

    print("📌 All Clients: $allClients");
    print("📌 Raw Daily Sales Data Before Processing: $salesData");

    List<Map<String, dynamic>> completeData = allClients.map((client) {
      var matchingSales = salesData.firstWhere(
              (sale) => sale["client_id"] == client["client_id"],  // ✅ client_id 기준으로 매칭
          orElse: () => {
            "client_id": client["client_id"],
            "client_name": client["client_name"],  // ✅ `client_name` 유지
            "products": [],  // ✅ 빈 제품 리스트 추가
            "total_sales": 0.0,
            "outstanding": outstandingMap[client["client_name"]] ?? 0
          }
      );

      return {
        "client_id": client["client_id"],
        "client_name": client["client_name"],
        "total_boxes": matchingSales.containsKey("products")
            ? matchingSales["products"].fold(0, (sum, item) => sum + (item["quantity"] ?? 0))  // ✅ `products[].quantity` 값 합산
            : 0,
        "total_sales": matchingSales["total_sales"] ?? 0.0,
        "outstanding": outstandingMap[client["client_name"]] ?? 0
      };
    }).toList();

    print("📌 Processed Daily Sales Data: $completeData");
    return completeData;
  }


  Future<List<Map<String, dynamic>>> _processMonthlySales(List<dynamic> salesData) async {
    await _fetchOutstandingData();
    var allClients = await salesService.fetchAllClients(widget.token, widget.employeeId);

    print("📌 All Clients: $allClients");
    print("📌 Raw Monthly Sales Data Before Processing: $salesData");

    List<Map<String, dynamic>> completeData = allClients.map((client) {
      var matchingSales = salesData.firstWhere(
              (sale) => sale["client_name"] == client["client_name"],
          orElse: () => {
            "client_name": client["client_name"],
            "total_boxes": 0,
            "total_sales": 0,
            "outstanding": outstandingMap[client["client_name"]] ?? 0,
            ...Map.fromEntries(List.generate(31, (i) => MapEntry("${i + 1}", 0))),
          }
      );

      return {
        "client_name": client["client_name"],
        "total_boxes": matchingSales["total_boxes"] ?? 0,
        "total_sales": matchingSales["total_sales"] ?? 0,
        "outstanding": outstandingMap[client["client_name"]] ?? 0,
        ...Map.fromEntries(List.generate(31, (i) => MapEntry("${i + 1}", matchingSales.containsKey("${i + 1}") ? matchingSales["${i + 1}"] : 0))),
      };
    }).toList();

    print("📌 Processed Monthly Sales Data: $completeData");
    return completeData;
  }
  Future<List<Map<String, dynamic>>> _processYearlySales(List<dynamic> salesData) async {
    await _fetchOutstandingData();
    var allClients = await salesService.fetchAllClients(widget.token, widget.employeeId);

    print("📌 All Clients: $allClients");
    print("📌 Raw Yearly Sales Data Before Processing: $salesData");

    List<Map<String, dynamic>> completeData = allClients.map((client) {
      var matchingSales = salesData.firstWhere(
              (sale) => sale["client_name"] == client["client_name"],
          orElse: () => {
            "client_name": client["client_name"],
            "total_boxes": 0,
            "total_sales": 0,
            "outstanding": outstandingMap[client["client_name"]] ?? 0,
            ...Map.fromEntries(List.generate(12, (i) => MapEntry("${i + 1}월", 0))),
          }
      );

      return {
        "client_name": client["client_name"],
        "total_boxes": matchingSales["total_boxes"] ?? 0,
        "total_sales": matchingSales["total_sales"] ?? 0,
        "outstanding": outstandingMap[client["client_name"]] ?? 0,
        ...Map.fromEntries(List.generate(12, (i) => MapEntry("${i + 1}월", matchingSales.containsKey("${i + 1}월") ? matchingSales["${i + 1}월"] : 0))),
      };
    }).toList();

    print("📌 Processed Yearly Sales Data: $completeData");
    return completeData;
  }




  Future<List<Map<String, dynamic>>> _processSalesData(List<dynamic> salesData) async {
    await _fetchOutstandingData();
    var allClients = await salesService.fetchAllClients(widget.token, widget.employeeId);

    print("📌 All Clients: $allClients");
    print("📌 Raw Sales Data Before Processing: $salesData");

    List<Map<String, dynamic>> completeData = allClients.map((client) {
      // ✅ client_name을 기준으로 매핑해야 함
      var matchingSales = salesData.firstWhere(
              (sale) => sale["client_name"] == client["client_name"], // ✅ client_name으로 비교
          orElse: () => {
            "index": client["client_name"],  // ✅ client_name을 기준으로 매핑
            "client_name": client["client_name"],
            "total_boxes": 0,
            "total_refunds": 0.0,
            "total_sales": 0.0,
            "outstanding": outstandingMap[client["client_name"]] ?? 0,
            ...Map.fromEntries(List.generate(12, (i) => MapEntry("${i + 1}월", 0))), // ✅ 1~12월 데이터 추가
          }
      );

      return {
        "index": matchingSales["index"] ?? client["client_name"], // ✅ 순번 유지
        "client_name": client["client_name"],
        "total_boxes": matchingSales["total_boxes"] ?? 0,
        "total_refunds": matchingSales["total_refunds"] ?? 0.0,
        "total_sales": matchingSales["total_sales"] ?? 0.0,
        "outstanding": outstandingMap[client["client_name"]] ?? 0,
        ...Map.fromEntries(List.generate(12, (i) => MapEntry("${i + 1}월", matchingSales.containsKey("${i + 1}월") ? matchingSales["${i + 1}월"] : 0))), // ✅ 월별 데이터 유지
      };
    }).toList();

    print("📌 Processed Data: $completeData"); // ✅ 최종적으로 UI에 전달되는 데이터 확인
    return completeData;
  }







  /// ✅ 거래처 미수금 데이터를 별도로 가져오는 함수
  Future<void> _fetchOutstandingData() async {
    try {
      var outstandingData = await salesService.fetchOutstanding(widget.token, widget.employeeId);

      print("📌 Fetched Outstanding Data (After UTF-8 Fix): $outstandingData");

      setState(() {
        outstandingMap = Map.fromIterable(
          outstandingData,
          key: (item) => item["client_name"].toString().trim(),
          value: (item) => (item["outstanding"] as num?)?.toInt() ?? 0,
        );
      });

      print("📌 Parsed Outstanding Map: $outstandingMap");
    } catch (e) {
      print("❌ 미수금 데이터를 가져오는 중 오류 발생: $e");
    }
  }






  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        elevation: 3,
        leading: IconButton(
          icon: const Icon(Icons.home, color: Colors.white),
          onPressed: () {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => HomeScreen(token: widget.token)),
                  (route) => false,
            );
          },

        ),
        title: const Text(
          "실적 현황",
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.print, color: Colors.white),
            onPressed: () {
              // 인쇄 기능 추가 예정
            },
          ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildSalesTypeSelector(),
          _buildDateSelector(),
          const Divider(height: 1, thickness: 1),
          Expanded(
            child: FutureBuilder<List<dynamic>>(
              future: salesData,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return const Center(child: Text("데이터를 불러오는 중 오류 발생"));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(child: Text("데이터가 없습니다."));
                } else {
                  return _buildSalesTable(snapshot.data!);
                }
              },
            ),
          ),
        ],
      ),
    );
  }

  /// ✅ 미수금 값이 존재하면 표시, 없으면 0으로 기본값 설정
  /// ✅ UTF-8 디코딩 후 미수금 가져오기
  /// ✅ UTF-8 디코딩 제거
  String _getOutstanding(String clientName) {
    String trimmedName = clientName.trim();
    if (outstandingMap.containsKey(trimmedName)) {
      return outstandingMap[trimmedName].toString();
    }
    return "0"; // ✅ 매칭되지 않으면 0 반환
  }




  /// 1. 매출 유형 선택 라디오 버튼
  Widget _buildSalesTypeSelector() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: ["일매출", "월매출", "년매출"].map((type) {
        return Row(
          children: [
            Radio<String>(
              value: type,
              groupValue: selectedType,
              onChanged: (value) {
                setState(() {
                  selectedType = value!;
                  _fetchSalesData();
                });
              },
            ),
            Text(type),
          ],
        );
      }).toList(),
    );
  }

  /// 2. 날짜 선택
  Widget _buildDateSelector() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          TextButton(
            onPressed: () async {
              DateTime? pickedDate = await showDatePicker(
                context: context,
                initialDate: selectedDate,
                firstDate: DateTime(2020),
                lastDate: DateTime.now(),
              );
              if (pickedDate != null) {
                setState(() {
                  selectedDate = pickedDate;
                  _fetchSalesData();
                });
              }
            },
            child: Text("${selectedDate.year}-${selectedDate.month}-${selectedDate.day}"),
          ),
        ],
      ),
    );
  }

  /// 3. 매출 데이터 테이블 (스타일 적용)
  Widget _buildSalesTable(List<dynamic> data) {
    List<DataRow> rows = _getRows(data);
    List<DataColumn> columns = _getColumns(); // ✅ 컬럼 개수 가져오기

    print("📌 Columns Count: ${columns.length}");

    // ✅ Flutter에서 매출 합계 계산
    int totalBoxes = 0;
    int totalOutstanding = 0;
    int totalSales = 0;
    List<int> dailyTotals = List.filled(31, 0); // ✅ 월별 일자별 합계

    for (var row in data) {
      totalBoxes += (row["total_boxes"] as num? ?? 0).toInt();
      totalSales += (row["total_sales"] as num? ?? 0).toInt();

      if (selectedType != "일매출") {
        // ✅ "일매출"에서는 미수금 합산하지 않음
        totalOutstanding += (row["outstanding"] as num? ?? 0).toInt();
      }

      if (selectedType == "월매출") {
        for (int i = 1; i <= 31; i++) {
          String key = "$i";
          dailyTotals[i - 1] += (row.containsKey(key) ? (row[key] as num? ?? 0).toInt() : 0);
        }
      }
    }

    print("📌 Total Sales (Flutter Calculated): $totalSales");
    print("📌 Total Outstanding (Flutter Calculated): $totalOutstanding");

    // ✅ 합계 행 추가
    List<DataCell> totalCells = [];

    if (selectedType == "일매출" || selectedType == "년매출") {
      // ✅ 첫 번째 열(순번)과 두 번째 열(거래처명)은 비우고 시작
      totalCells.add(DataCell(Text("")));
      totalCells.add(DataCell(Text("합계", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16))));

      // ✅ 나머지 데이터 한 칸씩 뒤로 밀어서 추가
      totalCells.add(DataCell(Text(totalBoxes.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text("0", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)))); // ✅ "일매출"에서는 미수금 0
      totalCells.add(DataCell(Text(totalSales.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
    } else if (selectedType == "월매출") {
      totalCells.add(DataCell(Text("합계", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16))));

      totalCells.addAll(dailyTotals.map((sum) => DataCell(Text(sum.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)))));
      totalCells.add(DataCell(Text(totalBoxes.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text(totalOutstanding.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text(totalSales.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
    }

    while (totalCells.length < columns.length) {
      totalCells.add(DataCell(Text("")));
    }

    rows.add(DataRow(
      color: MaterialStateProperty.all(Colors.blueGrey[100]),
      cells: totalCells,
    ));

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SingleChildScrollView(
        scrollDirection: Axis.vertical,
        child: DataTable(
          headingRowColor: MaterialStateProperty.all(Colors.blueGrey[800]),
          headingTextStyle: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
            color: Colors.white,
          ),
          columnSpacing: 20,
          border: TableBorder.all(color: Colors.grey.shade400),
          columns: columns,
          rows: rows,
        ),
      ),
    );
  }



  List<DataColumn> _getColumns() {
    if (selectedType == "일매출") {
      return [
        DataColumn(label: _buildHeaderText("순번")),
        DataColumn(label: _buildHeaderText("거래처명")),
        DataColumn(label: _buildHeaderText("판매박스수")),
        DataColumn(label: _buildHeaderText("미수금")),
        DataColumn(label: _buildHeaderText("매출")),
      ];
    } else if (selectedType == "월매출") {
      return [
        DataColumn(label: _buildHeaderText("거래처명")),
        ...List.generate(31, (day) => DataColumn(label: _buildHeaderText("${day + 1}일"))),
        DataColumn(label: _buildHeaderText("판매박스수")),
        DataColumn(label: _buildHeaderText("미수금")),
        DataColumn(label: _buildHeaderText("매출")),
      ];
    } else {
      return [
        DataColumn(label: _buildHeaderText("순번")),
        DataColumn(label: _buildHeaderText("거래처명")),
        DataColumn(label: _buildHeaderText("판매박스수")),
        DataColumn(label: _buildHeaderText("반품금액")),
        DataColumn(label: _buildHeaderText("매출")),
      ];
    }
  }
  /// ✅ 테이블 헤더 텍스트 스타일
  Widget _buildHeaderText(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Text(
        text,
        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
        textAlign: TextAlign.center,
      ),
    );
  }
  /// ✅ 데이터 행 스타일 적용 함수
  /// ✅ 데이터 행 스타일 적용 함수
  List<DataRow> _getRows(List<dynamic> data) {
    List<DataColumn> columns = _getColumns(); // ✅ 컬럼 개수 가져오기

    return List.generate(data.length, (index) {
      var row = data[index];

      String clientName = row["client_name"] ?? "-";
      String outstanding = _getOutstanding(clientName);
      int totalSales = (row["total_sales"] as num? ?? 0).toInt();

      // ✅ "일매출" 선택 시, 매출이 0인 거래처는 제외
      if (selectedType == "일매출" && totalSales == 0) {
        return null; // 매출이 0이면 리스트에 추가하지 않음
      }

      List<DataCell> cells = [];

      if (selectedType == "일매출") {
        cells = [
          DataCell(Text("${index + 1}")),
          DataCell(Text(clientName)),
          DataCell(Text(row["total_boxes"]?.toString() ?? "0")),
          DataCell(Text(outstanding)),
          DataCell(Text(totalSales.toString())),
        ];
      } else if (selectedType == "월매출") {
        cells.add(DataCell(Text(clientName)));

        for (int i = 1; i <= 31; i++) {
          String key = "$i";
          cells.add(DataCell(Text(row.containsKey(key) ? row[key].toString() : "0"))); // ✅ 날짜별 매출 유지
        }

        cells.add(DataCell(Text(row["total_boxes"]?.toString() ?? "0")));
        cells.add(DataCell(Text(outstanding)));
        cells.add(DataCell(Text(totalSales.toString())));
      } else {
        cells = [
          DataCell(Text("${index + 1}")),
          DataCell(Text(clientName)),
          DataCell(Text(row["total_boxes"]?.toString() ?? "0")),
          DataCell(Text(row["total_refunds"]?.toString() ?? "0")),
          DataCell(Text(totalSales.toString())),
        ];
      }

      while (cells.length < columns.length) {
        cells.add(DataCell(Text("")));
      }

      return DataRow(
        color: MaterialStateProperty.resolveWith<Color?>(
              (Set<MaterialState> states) {
            if (index.isEven) return Colors.grey[200];
            return Colors.white;
          },
        ),
        cells: cells,
      );
    }).whereType<DataRow>().toList(); // ✅ null 값 필터링
  }



  /// 4. 인쇄 버튼
  Widget _buildPrintButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: ElevatedButton.icon(
        onPressed: () {},
        icon: Icon(Icons.print),
        label: Text("인쇄"),
      ),
    );
  }
}

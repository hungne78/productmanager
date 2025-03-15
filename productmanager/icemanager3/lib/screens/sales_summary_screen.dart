import 'package:flutter/material.dart';
import '../services/sales_service.dart';
import 'dart:convert'; // ✅ UTF-8 디코딩을 위해 필요

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
  final SalesService salesService = SalesService("http://192.168.50.221:8000");

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
          return _processSalesData(data);
        });
      } else if (selectedType == "월매출") {
        salesData = salesService.fetchMonthlySales(
            widget.token, widget.employeeId, selectedDate.year, selectedDate.month
        ).then((data) {
          return _processSalesData(data);
        });
      } else {
        salesData = salesService.fetchYearlySales(
            widget.token, widget.employeeId, selectedDate.year
        ).then((data) {
          return _processSalesData(data);
        });
      }
    });
  }


  Future<List<Map<String, dynamic>>> _processSalesData(List<dynamic> salesData) async {
    // ✅ 미수금 데이터 가져오기
    await _fetchOutstandingData();

    // ✅ 모든 거래처 리스트 가져오기 (매출이 없는 경우 0으로 설정)
    var allClients = await salesService.fetchAllClients(widget.token, widget.employeeId);

    // ✅ 거래처 목록을 매출 데이터와 병합하여 날짜별 데이터 유지
    List<Map<String, dynamic>> completeData = allClients.map((client) {
      var matchingSales = salesData.firstWhere(
              (sale) => sale["client_name"] == client["client_name"],
          orElse: () => {
            "client_name": client["client_name"],
            "total_boxes": 0,
            "total_sales": 0,
            "outstanding": outstandingMap[client["client_name"]] ?? 0,
            ...Map.fromEntries(List.generate(31, (i) => MapEntry("${i + 1}", 0))), // ✅ 1~31일 데이터 초기화 (오류 해결)
          }
      );

      return {
        "client_name": client["client_name"],
        "total_boxes": matchingSales["total_boxes"] ?? 0,
        "total_sales": matchingSales["total_sales"] ?? 0,
        "outstanding": outstandingMap[client["client_name"]] ?? 0, // ✅ 미수금 포함
        ...Map.fromEntries(List.generate(31, (i) => MapEntry("${i + 1}", matchingSales.containsKey("${i + 1}") ? matchingSales["${i + 1}"] : 0))), // ✅ 날짜별 매출 유지
      };
    }).toList();

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
      appBar: AppBar(title: Text("실적 종합 현황")),
      body: Column(
        children: [
          _buildSalesTypeSelector(),
          _buildDateSelector(),
          Expanded(
            child: FutureBuilder<List<dynamic>>(
              future: salesData,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return Center(child: CircularProgressIndicator());
                } else if (snapshot.hasError) {
                  return Center(child: Text("데이터를 불러오는 중 오류 발생"));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return Center(child: Text("데이터가 없습니다."));
                } else {
                  return _buildSalesTable(snapshot.data!);
                }
              },
            ),
          ),
          _buildPrintButton(),
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
      totalOutstanding += (row["outstanding"] as num? ?? 0).toInt();
      totalSales += (row["total_sales"] as num? ?? 0).toInt();

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

    // ✅ 매출 유형별로 합계 행 처리 방식 다르게 적용
    if (selectedType == "일매출" || selectedType == "년매출") {
      // ✅ 첫 번째 열(순번)과 두 번째 열(거래처명)은 비우고 시작
      totalCells.add(DataCell(Text("")));
      totalCells.add(DataCell(Text("합계", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16))));

      // ✅ 나머지 데이터 한 칸씩 뒤로 밀어서 추가
      totalCells.add(DataCell(Text(totalBoxes.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text(totalOutstanding.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text(totalSales.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
    } else if (selectedType == "월매출") {
      // ✅ 첫 번째 열(거래처명 자리)에는 '합계' 추가
      totalCells.add(DataCell(Text("합계", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16))));

      // ✅ 월매출에서는 1~31일 합계 추가
      totalCells.addAll(dailyTotals.map((sum) => DataCell(Text(sum.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)))));

      // ✅ 나머지 합계 정보 추가
      totalCells.add(DataCell(Text(totalBoxes.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text(totalOutstanding.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
      totalCells.add(DataCell(Text(totalSales.toString(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14))));
    }

    // ✅ 부족한 셀을 빈 값으로 채워 정렬 유지
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
        DataColumn(label: _buildHeaderText("미수금")),
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
  List<DataRow> _getRows(List<dynamic> data) {
    List<DataColumn> columns = _getColumns(); // ✅ 컬럼 개수 가져오기

    return List.generate(data.length, (index) {
      var row = data[index];

      String clientName = row["client_name"] ?? "-";
      String outstanding = _getOutstanding(clientName);

      List<DataCell> cells = [];

      if (selectedType == "일매출") {
        cells = [
          DataCell(Text("${index + 1}")),
          DataCell(Text(clientName)),
          DataCell(Text(row["total_boxes"]?.toString() ?? "0")),
          DataCell(Text(outstanding)),
          DataCell(Text(row["total_sales"]?.toString() ?? "0")),
        ];
      } else if (selectedType == "월매출") {
        cells.add(DataCell(Text(clientName)));

        for (int i = 1; i <= 31; i++) {
          String key = "$i";
          cells.add(DataCell(Text(row.containsKey(key) ? row[key].toString() : "0"))); // ✅ 날짜별 매출 유지
        }

        cells.add(DataCell(Text(row["total_boxes"]?.toString() ?? "0")));
        cells.add(DataCell(Text(outstanding)));
        cells.add(DataCell(Text(row["total_sales"]?.toString() ?? "0")));
      } else {
        cells = [
          DataCell(Text("${index + 1}")),
          DataCell(Text(clientName)),
          DataCell(Text(row["total_boxes"]?.toString() ?? "0")),
          DataCell(Text(row["total_refunds"]?.toString() ?? "0")),
          DataCell(Text(row["total_sales"]?.toString() ?? "0")),
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
    });
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

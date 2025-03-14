import 'package:flutter/material.dart';
import '../services/sales_service.dart';

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
  final SalesService salesService = SalesService("http://192.168.0.183:8000");

  Future<List<dynamic>>? salesData;

  @override
  void initState() {
    super.initState();
    _fetchSalesData();
  }

  void _fetchSalesData() {
    setState(() {
      if (selectedType == "일매출") {
        salesData = salesService.fetchDailySales(
            widget.token, widget.employeeId, selectedDate.toString().split(' ')[0]);
      } else if (selectedType == "월매출") {
        salesData = salesService
            .fetchMonthlySales(widget.token, widget.employeeId, selectedDate.year, selectedDate.month)
            .then((data) => data is List<Map<String, dynamic>> ? data : []);
      } else {
        salesData = salesService
            .fetchYearlySales(widget.token, widget.employeeId, selectedDate.year)
            .then((data) => data is List<Map<String, dynamic>> ? data : []);
      }
    });
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

  /// 3. 매출 데이터 테이블
  Widget _buildSalesTable(List<dynamic> data) {
    return SingleChildScrollView(
      scrollDirection: selectedType == "월매출" ? Axis.horizontal : Axis.vertical,
      child: DataTable(
        columns: _getColumns(),
        rows: _getRows(data),
      ),
    );
  }

  List<DataColumn> _getColumns() {
    if (selectedType == "일매출") {
      return [
        DataColumn(label: Text("순번")),
        DataColumn(label: Text("거래처명")),
        DataColumn(label: Text("판매박스수")),
        DataColumn(label: Text("미수금")),
        DataColumn(label: Text("매출")),
      ];
    } else if (selectedType == "월매출") {
      return [
        DataColumn(label: Text("거래처명")),
        ...List.generate(31, (day) => DataColumn(label: Text("${day + 1}일"))),
        DataColumn(label: Text("판매박스수")),
        DataColumn(label: Text("미수금")),
        DataColumn(label: Text("매출")),
      ];
    } else {
      return [
        DataColumn(label: Text("순번")),
        DataColumn(label: Text("거래처명")),
        DataColumn(label: Text("판매박스수")),
        DataColumn(label: Text("반품금액")),
        DataColumn(label: Text("매출")),
      ];
    }
  }

  List<DataRow> _getRows(List<dynamic> data) {
    return List.generate(data.length, (index) {
      var row = data[index];
      if (selectedType == "일매출") {
        return DataRow(cells: [
          DataCell(Text("${index + 1}")),
          DataCell(Text(row["client_name"])),
          DataCell(Text(row["total_boxes"].toString())),
          DataCell(Text(row["outstanding"].toString())),
          DataCell(Text(row["total_sales"].toString())),
        ]);
      } else {
        return DataRow(cells: row.map((cell) => DataCell(Text(cell.toString()))).toList());
      }
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

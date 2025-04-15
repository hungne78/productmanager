// lib/screens/clients/client_detail_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/client_api_service.dart';
import 'package:intl/intl.dart';

class ClientDetailScreen extends StatefulWidget {
  final int clientId;
  const ClientDetailScreen({Key? key, required this.clientId}) : super(key: key);

  @override
  _ClientDetailScreenState createState() => _ClientDetailScreenState();
}

class _ClientDetailScreenState extends State<ClientDetailScreen> {
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _client; // 기본정보
  double _totalOutstanding = 0.0;
  List<Map<String, dynamic>> _recentSales = [];
  List<Map<String, dynamic>> _visits = [];
  List<Map<String, dynamic>> _employees = []; // 담당 직원들

  @override
  void initState() {
    super.initState();
    _fetchClientDetail();
  }

  Future<void> _fetchClientDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _client = null;
      _recentSales.clear();
      _visits.clear();
      _employees.clear();
      _totalOutstanding = 0.0;
    });

    final token = context.read<AuthProvider>().token;
    if (token == null) {
      setState(() {
        _isLoading = false;
        _error = "로그인이 필요합니다.";
      });
      return;
    }

    try {
      final data = await ClientApiService.fetchClientDetail(token, widget.clientId);
      // data 예:
      // {
      //   "client_id":101,
      //   "client_name":"ABC상점", "representative":"홍길동", "business_number":"123-45-67890",
      //   "address":"서울시 ...",
      //   "phone":"02-1234-5678",
      //   "outstanding":50000,
      //   "employees":[ {"employee_id":1,"employee_name":"김영업"}, ...],
      //   "recent_sales":[{"date":"2025-05-01","amount":30000,"products":[...]}, ...],
      //   "visits":[{"date":"2025-05-02","employee_id":1}, ...]
      // }
      setState(() {
        _client = data;
        _totalOutstanding = (data["outstanding"] ?? 0).toDouble();
        _employees = List<Map<String, dynamic>>.from(data["employees"] ?? []);
        _recentSales = List<Map<String, dynamic>>.from(data["recent_sales"] ?? []);
        _visits = List<Map<String, dynamic>>.from(data["visits"] ?? []);
      });
    } catch (e) {
      setState(() => _error = "거래처 상세조회 실패: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = NumberFormat("#,###");
    return Scaffold(
      appBar: AppBar(
        title: Text("거래처 상세 (ID: ${widget.clientId})"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
          : _client == null
          ? const Center(child: Text("거래처 정보를 불러올 수 없습니다."))
          : SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildBasicInfoCard(),
            const SizedBox(height: 12),
            _buildOutstandingCard(f),
            const SizedBox(height: 12),
            _buildEmployeesCard(),
            const SizedBox(height: 12),
            _buildRecentSalesCard(f),
            const SizedBox(height: 12),
            _buildVisitsCard(),

            ExpansionTile(
              title: const Text("📊 거래처 월별 통계"),
              children: [
                FutureBuilder(
                  future: _loadMonthlyClientStats(widget.clientId),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const Padding(
                        padding: EdgeInsets.all(16.0),
                        child: Center(child: CircularProgressIndicator()),
                      );
                    }

                    if (snapshot.hasError) {
                      return Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Text("통계 로딩 실패: ${snapshot.error}"),
                      );
                    }

                    final stats = snapshot.data as List<Map<String, dynamic>>;
                    return _buildMonthlySummaryTable(stats);
                  },
                )
              ],
            ),

          ],

        ),
      ),
    );
  }
  Future<List<Map<String, dynamic>>> _loadMonthlyClientStats(int clientId) async {
    final now = DateTime.now();
    final year = now.year;

    final token = context.read<AuthProvider>().token!;
    final sales = await ClientApiService.fetchMonthlySales(clientId, year, token);
    final visits = await ClientApiService.fetchMonthlyVisits(clientId, year, token);
    final boxes = await ClientApiService.fetchMonthlyBoxCount(clientId, year, token); // 직접 구현 필요

    List<Map<String, dynamic>> stats = List.generate(12, (i) => {
      "month": i + 1,
      "sales": sales[i],
      "visits": visits[i],
      "boxes": boxes[i],
    });

    return stats;
  }

  Widget _buildMonthlySummaryTable(List<Map<String, dynamic>> stats) {
    final f = NumberFormat("#,###");
    return DataTable(
      columns: const [
        DataColumn(label: Text('월')),
        DataColumn(label: Text('매출액')),
        DataColumn(label: Text('방문 수')),
        DataColumn(label: Text('박스 수')),
      ],
      rows: stats.map((m) {
        final month = m["month"];
        final sales = m["sales"];
        final visits = m["visits"];
        final boxes = m["boxes"];
        return DataRow(
          cells: [
            DataCell(Text("$month월")),
            DataCell(Text("${f.format(sales ?? 0)} 원")),
            DataCell(Text("${visits ?? 0} 회")),
            DataCell(Text("${boxes ?? 0} 박스")),
          ],
        );
      }).toList(),
    );
  }

  Widget _buildBasicInfoCard() {
    return Card(
      child: ListTile(
        title: Text(_client?["client_name"] ?? "이름 없음", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("대표자: ${_client?["representative"] ?? "-"}"),
            Text("사업자번호: ${_client?["business_number"] ?? "-"}"),
            Text("전화번호: ${_client?["phone"] ?? "-"}"),
            Text("주소: ${_client?["address"] ?? "-"}"),
          ],
        ),
      ),
    );
  }

  Widget _buildOutstandingCard(NumberFormat f) {
    return Card(
      child: ListTile(
        title: const Text("미수금"),
        trailing: Text("${f.format(_totalOutstanding)} 원",
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildEmployeesCard() {
    if (_employees.isEmpty) {
      return const Card(child: ListTile(title: Text("담당 직원 없음")));
    }
    return Card(
      child: Column(
        children: [
          const ListTile(
            title: Text("담당 영업사원(들)", style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          const Divider(height: 1),
          ..._employees.map((e) {
            final empName = e["employee_name"] ?? "이름없음";
            return ListTile(
              leading: const Icon(Icons.person),
              title: Text(empName),
              subtitle: Text("직원 ID: ${e["employee_id"]}"),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildRecentSalesCard(NumberFormat f) {
    if (_recentSales.isEmpty) {
      return const Card(child: ListTile(title: Text("최근 매출 내역 없음")));
    }
    return Card(
      child: Column(
        children: [
          const ListTile(
            title: Text("최근 매출 내역", style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          const Divider(height: 1),
          ..._recentSales.map((sale) {
            final date = sale["date"] ?? "";
            final amount = sale["amount"] ?? 0;
            return ListTile(
              leading: const Icon(Icons.sell),
              title: Text("$date"),
              trailing: Text("${f.format(amount)} 원"),
              // 눌렀을 때 판매 상세로 이동할 수도 있음
              // onTap: () => ...
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildVisitsCard() {
    if (_visits.isEmpty) {
      return const Card(child: ListTile(title: Text("최근 방문 기록 없음")));
    }
    return Card(
      child: Column(
        children: [
          const ListTile(
            title: Text("최근 방문 기록", style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          const Divider(height: 1),
          ..._visits.map((v) {
            final date = v["date"] ?? "";
            final empId = v["employee_id"];
            return ListTile(
              leading: const Icon(Icons.location_on),
              title: Text("$date"),
              subtitle: Text("직원 ID: $empId"),
            );
          }).toList(),
        ],
      ),
    );
  }
}

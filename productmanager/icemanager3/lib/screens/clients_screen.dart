import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';
import 'package:intl/intl.dart'; // ✅ 천 단위 콤마 포맷 추가

class ClientsScreen extends StatefulWidget {
  final String token;
  final int employeeId;

  const ClientsScreen({Key? key, required this.token, required this.employeeId}) : super(key: key);

  @override
  _ClientsScreenState createState() => _ClientsScreenState();
}

class _ClientsScreenState extends State<ClientsScreen> {
  List<dynamic> _clients = [];
  Map<int, bool> _expandedRows = {}; // 확장된 행 추적
  Map<int, Map<String, dynamic>> _clientDetails = {}; // 개별 거래처 상세 정보 저장
  final NumberFormat formatter = NumberFormat("#,###"); // ✅ 천 단위 콤마 포맷

  @override
  void initState() {
    super.initState();
    _fetchEmployeeClients();
  }

  Future<void> _fetchEmployeeClients() async {
    try {
      final List<dynamic> clients = await ApiService.fetchEmployeeClients(widget.token, widget.employeeId);
      setState(() {
        _clients = clients;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("거래처 목록을 불러오는 데 실패했습니다: $e")),
      );
    }
  }

  Future<void> _fetchClientDetails(int clientId) async {
    if (_clientDetails.containsKey(clientId)) return;

    try {
      final Map<String, dynamic> data = await ApiService.fetchClientDetailsById(widget.token, clientId);
      setState(() {
        _clientDetails[clientId] = data;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("거래처 정보를 가져오는 데 실패했습니다: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("담당 거래처 관리")),
      body: ListView.builder(
        itemCount: _clients.length,
        itemBuilder: (context, index) {
          final client = _clients[index];
          final clientId = client['id'];
          final isExpanded = _expandedRows[clientId] ?? false;
          final details = _clientDetails[clientId];

          // ✅ 미수금 정수 변환 후 천 단위 콤마 적용
          final int outstandingAmount = (client['outstanding_amount'] ?? 0).toInt();
          final String formattedAmount = formatter.format(outstandingAmount);

          return Column(
            children: [
              // ✅ 기본 거래처 정보 (거래처명, 전화번호, 미수금)
              ListTile(
                tileColor: Colors.white,
                contentPadding: EdgeInsets.symmetric(vertical: 5, horizontal: 15),
                shape: RoundedRectangleBorder(
                  side: BorderSide(color: Colors.grey.shade300, width: 1),
                  borderRadius: BorderRadius.circular(5),
                ),
                title: Text(
                  client['client_name'],
                  style: TextStyle(fontWeight: FontWeight.bold),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(
                  "대표자: ${client['representative_name'] ?? '정보 없음'}  |  전화번호: ${client['phone'] ?? '정보 없음'}  |  미수금: ${formattedAmount} 원",
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: Icon(isExpanded ? Icons.expand_less : Icons.expand_more, color: Colors.blue),
                onTap: () {
                  setState(() {
                    _expandedRows[clientId] = !isExpanded;
                  });
                  if (!isExpanded) {
                    _fetchClientDetails(clientId);
                  }
                },
              ),

              // ✅ 클릭한 거래처의 확장 정보 (해당 거래처 아래에 바로 표시)
              if (isExpanded)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 5.0, horizontal: 10.0),
                  child: Container(
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.blue.shade300, width: 2),
                      borderRadius: BorderRadius.circular(8),
                      color: Colors.blue.shade50,
                    ),
                    padding: const EdgeInsets.all(12),
                    child: details == null
                        ? const Center(child: CircularProgressIndicator()) // 로딩 표시
                        : Table(
                      border: TableBorder.all(color: Colors.blue.shade200),
                      columnWidths: const {
                        0: FractionColumnWidth(0.3),
                        1: FractionColumnWidth(0.7),
                      },
                      children: [
                        _buildTableRow("대표자", details['representative_name'] ?? '정보 없음'),  // ✅ 대표자 추가
                        _buildTableRow("주소", details['address'] ?? '정보 없음'),
                        _buildTableRow("사업자 번호", details['business_number'] ?? '정보 없음'),
                        _buildTableRow("이메일", details['email'] ?? '정보 없음'),
                        _buildTableRow("일반가", details['regular_price']?.toString() ?? '정보 없음'),
                        _buildTableRow("고정가", details['fixed_price']?.toString() ?? '정보 없음'),

                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  // ✅ 거래처 확장 정보 테이블의 한 행을 구성하는 함수
  TableRow _buildTableRow(String title, String value) {
    return TableRow(
      children: [
        _buildTableCell(title, isHeader: true),
        _buildTableCell(value),
      ],
    );
  }

  // ✅ 거래처 확장 정보의 셀 스타일
  Widget _buildTableCell(String text, {bool isHeader = false}) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Text(
        text,
        style: TextStyle(
          fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
          fontSize: isHeader ? 15 : 14,
          color: isHeader ? Colors.black : Colors.blue.shade900,
        ),
      ),
    );
  }
}

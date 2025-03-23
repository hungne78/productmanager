import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';
import 'package:intl/intl.dart'; // ✅ 천 단위 콤마 포맷 추가
import '../screens/home_screen.dart';
import 'package:url_launcher/url_launcher.dart';

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
  Future<void> _makePhoneCall(String? phoneNumber) async {
    if (phoneNumber == null) return;
    final Uri url = Uri.parse('tel:$phoneNumber');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      throw '전화 앱을 실행할 수 없습니다.';
    }
  }

  void _showPhoneOptions(String? phone) {
    if (phone == null) return;

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) {
        return Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.call),
              title: const Text("전화 걸기"),
              onTap: () {
                Navigator.pop(context);
                _makePhoneCall(phone);
              },
            ),
            ListTile(
              leading: const Icon(Icons.message),
              title: const Text("문자 보내기"),
              onTap: () {
                Navigator.pop(context);
                _sendSms(phone);
              },
            ),
          ],
        );
      },
    );
  }
  Future<void> _sendSms(String phoneNumber) async {
    final Uri uri = Uri.parse('sms:$phoneNumber');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    } else {
      throw '메시지 앱을 열 수 없습니다.';
    }
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(56),
        child: AppBar(
          backgroundColor: Colors.indigo,
          elevation: 3,
          centerTitle: true,
          leading: IconButton(
            icon: const Icon(Icons.home, color: Colors.white),
            onPressed: () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (_) => HomeScreen(token: widget.token),
                ),
              );
            },
          ),
          title: const Text(
            "담당 거래처 관리",
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 18,
              color: Colors.white,
            ),
          ),
        ),
      ),
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
              Card(
                elevation: 2,
                margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                child: ListTile(
                  tileColor: Colors.white,
                  contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                  title: Text(
                    client['client_name'],
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  subtitle: Row(
                    children: [
                      GestureDetector(
                        onTap: () => _showPhoneOptions(client['phone']),
                        child: Row(
                          children: [
                            const Icon(Icons.phone, size: 16, color: Colors.blue),
                            const SizedBox(width: 4),
                            Text(
                              client['phone'] ?? '정보 없음',
                              style: const TextStyle(fontSize: 13, color: Colors.blue),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(width: 10),
                      Text("•  미수금: ${formattedAmount} 원", style: TextStyle(fontSize: 13, color: Colors.grey.shade800)),
                    ],
                  ),
                  trailing: GestureDetector(
                    onTap: () {
                      setState(() {
                        _expandedRows[clientId] = !isExpanded;
                      });
                      if (!isExpanded) _fetchClientDetails(clientId);
                    },
                    child: Icon(
                      isExpanded ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                      color: Colors.indigo,
                      size: 28,
                    ),
                  ),
                  // 전체 onTap 제거
                  onTap: null,
                ),
              ),


              if (isExpanded)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.indigo.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.indigo.shade200),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: details == null
                        ? const Center(child: CircularProgressIndicator())
                        : Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _infoRow("👤 대표자", details['representative_name']),
                        _infoRow("🏢 주소", details['address']),
                        _infoRow("🧾 사업자 번호", details['business_number']),
                        _infoRow("📧 이메일", details['email']),
                        _infoRow("💵 일반가", details['regular_price']?.toString()),
                        _infoRow("📦 고정가", details['fixed_price']?.toString()),
                        _infoRow("💰 미수금", formattedAmount.toString()),
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
  Widget _infoRow(String label, String? value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "$label: ",
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
          ),
          Expanded(
            child: Text(
              value ?? '정보 없음',
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
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

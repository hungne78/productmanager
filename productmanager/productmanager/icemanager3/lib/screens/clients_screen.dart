import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:convert';
import 'package:intl/intl.dart'; // ✅ 천 단위 콤마 포맷 추가
import '../screens/home_screen.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:http/http.dart' as http;

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
                        const SizedBox(height: 12), // 여백
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            onPressed: () => _showLentFreezerModal(context, clientId, widget.token),
                            icon: const Icon(Icons.ac_unit),
                            label: const Text("대여 냉동고 보기"),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.indigo,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ),
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
  void _showLentFreezerModal(BuildContext context, int clientId, String token) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => LentFreezerBottomSheet(clientId: clientId, token: token),
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

class LentFreezerEditDialog extends StatefulWidget {
  final int clientId;
  final String token;
  final Map<String, dynamic>? freezer;

  const LentFreezerEditDialog({
    super.key,
    required this.clientId,
    required this.token,
    this.freezer,
  });

  @override
  State<LentFreezerEditDialog> createState() => _LentFreezerEditDialogState();
}
class _LentFreezerEditDialogState extends State<LentFreezerEditDialog> {
  final _brandController = TextEditingController();
  final _sizeController = TextEditingController();
  final _serialController = TextEditingController();
  final _yearController = TextEditingController();

  @override
  void initState() {
    super.initState();
    final f = widget.freezer;
    if (f != null) {
      _brandController.text = f['brand'] ?? '';
      _sizeController.text = f['size'] ?? '';
      _serialController.text = f['serial_number'] ?? '';
      _yearController.text = f['year']?.toString() ?? '';
    }
  }

  void _save() async {
    final data = {
      "client_id": widget.clientId,
      "brand": _brandController.text,
      "size": _sizeController.text,
      "serial_number": _serialController.text,
      "year": int.tryParse(_yearController.text) ?? 0,
    };

    final isUpdate = widget.freezer != null;
    final url = isUpdate
        ? '$baseUrl/lent/id/${widget.freezer!['id']}'
        : '$baseUrl/lent/${widget.clientId}';

    final response = await (isUpdate
        ? http.put(Uri.parse(url),
      headers: {
        "Authorization": "Bearer ${widget.token}",
        "Content-Type": "application/json"
      },
      body: json.encode(data),
    )
        : http.post(Uri.parse(url),
      headers: {
        "Authorization": "Bearer ${widget.token}",
        "Content-Type": "application/json"
      },
      body: json.encode(data),
    ));


    if (response.statusCode == 200 || response.statusCode == 201) {
      Navigator.pop(context, true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("저장 실패")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.freezer == null ? "냉동고 등록" : "냉동고 수정"),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(controller: _brandController, decoration: InputDecoration(labelText: "브랜드")),
          TextField(controller: _sizeController, decoration: InputDecoration(labelText: "사이즈")),
          TextField(controller: _serialController, decoration: InputDecoration(labelText: "시리얼번호")),
          TextField(controller: _yearController, decoration: InputDecoration(labelText: "년식"), keyboardType: TextInputType.number),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text("취소")),
        ElevatedButton(onPressed: _save, child: Text("저장")),
      ],
    );
  }
}
class LentFreezerBottomSheet extends StatefulWidget {
  final int clientId;
  final String token;

  const LentFreezerBottomSheet({super.key, required this.clientId, required this.token});

  @override
  State<LentFreezerBottomSheet> createState() => _LentFreezerBottomSheetState();
}

class _LentFreezerBottomSheetState extends State<LentFreezerBottomSheet> {
  late Future<List<Map<String, dynamic>>> _freezers;

  @override
  void initState() {
    super.initState();
    _freezers = ApiService.fetchLentFreezers(widget.clientId, widget.token);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(top: 16, bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text("대여 냉동고", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const Divider(),
          FutureBuilder<List<Map<String, dynamic>>>(
            future: _freezers,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Padding(
                  padding: EdgeInsets.all(24),
                  child: CircularProgressIndicator(),
                );
              }

              if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.all(24),
                  child: Text("등록된 냉동고가 없습니다."),
                );
              }

              final items = snapshot.data!;
              return Column(
                children: [
                  ...items.map((item) => ListTile(
                    title: Text("${item['brand']} (${item['size']})"),
                    subtitle: Text("시리얼: ${item['serial_number']} / 년식: ${item['year']}"),
                    // trailing: IconButton(                           //냉동고 수정
                    //   icon: const Icon(Icons.edit),
                    //   onPressed: () => _showEditDialog(item),
                    // ),
                  )),
                  // TextButton.icon(
                  //   onPressed: () => _showEditDialog(),              //냉동고 추가
                  //   icon: const Icon(Icons.add),
                  //   label: const Text("냉동고 추가"),
                  // ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  void _showEditDialog([Map<String, dynamic>? freezer]) async {
    final result = await showDialog(
      context: context,
      builder: (_) => LentFreezerEditDialog(
        clientId: widget.clientId,
        freezer: freezer,
        token: widget.token,
      ),
    );
    if (result == true) {
      setState(() {
        _freezers = ApiService.fetchLentFreezers(widget.clientId, widget.token);
      });
    }
  }
}


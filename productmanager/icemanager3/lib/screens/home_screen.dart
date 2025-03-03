import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import '../auth_provider.dart';
import '../services/api_service.dart';
import '../product_provider.dart';
import '../screens/sales_screen.dart';

class HomeScreen extends StatelessWidget {
  final String token;

  const HomeScreen({Key? key, required this.token}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text("메인화면"),
      ),
      body: Center(
        child: ElevatedButton.icon(
          icon: const Icon(Icons.shopping_cart),
          label: const Text("판매 시작"),
          onPressed: () {
            if (user == null) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("로그인이 필요합니다.")),
              );
              return;
            }
            _showClientSelectionDialog(context, user.token, user.id);
          },
        ),
      ),
    );
  }

  void _showClientSelectionDialog(BuildContext context, String token,
      int employeeId) async {
    List<dynamic> clients = [];
    bool isLoading = true;
    String? errorMessage;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext ctx) {
        return StatefulBuilder(
          builder: (context, setState) {
            if (isLoading) {
              _fetchEmployeeClients(token, employeeId).then((result) {
                setState(() {
                  clients = result['clients'];
                  isLoading = false;
                  errorMessage = result['error'];
                });
              });
            }

            return AlertDialog(
              title: const Text("거래처 선택"),
              content: isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : errorMessage != null
                  ? Text(errorMessage!)
                  : SingleChildScrollView(
                child: Column(
                  children: clients.map((client) {
                    return ListTile(
                      title: Text(client['client_name']),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("미수금: ${client['outstanding_amount']}원"),
                          Text("주소: ${client['address']}"),
                          Text("전화번호: ${client['phone']}"),
                          Text("사업자 번호: ${client['business_number']}"),
                          Text("이메일: ${client['email']}"),
                        ],
                      ),
                      onTap: () {
                        Navigator.of(ctx).pop(); // 팝업 닫기
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                SalesScreen(
                                  token: token,
                                  client: client, // 선택한 거래처 데이터 전달
                                ),
                          ),
                        );
                      },
                    );
                  }).toList(),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text("취소"),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<Map<String, dynamic>> _fetchEmployeeClients(String token,
      int employeeId) async {
    try {
      final resp = await ApiService.fetchEmployeeClients(token, employeeId);
      if (resp.statusCode == 200) {
        return {"clients": jsonDecode(resp.body), "error": null};
      } else {
        return {"clients": [], "error": "거래처 로드 실패: ${resp.statusCode}"};
      }
    } catch (e) {
      return {"clients": [], "error": "오류 발생: $e"};
    }
  }
}

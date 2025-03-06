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
      final clients = await ApiService.fetchEmployeeClients(
          token, employeeId); // ✅ List<dynamic> 직접 반환

      return {"clients": clients, "error": null};
    } catch (e) {
      return {"clients": [], "error": "오류 발생: $e"};
    }
  }

}
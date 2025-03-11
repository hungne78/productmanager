import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import '../auth_provider.dart';
import '../services/api_service.dart';
import '../product_provider.dart';
import '../screens/sales_screen.dart';
import '../screens/order_screen.dart';
import '../screens/clients_screen.dart';

import 'product_screen.dart';
import 'order_history_screen.dart';
class HomeScreen extends StatelessWidget {
  final String token;

  const HomeScreen({Key? key, required this.token}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    final productProvider = context.watch<ProductProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text("메인화면"),),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ElevatedButton.icon(
          icon: const Icon(Icons.refresh),
          label: const Text("상품 목록 업데이트"),
          onPressed: () async {
            final List<dynamic> products = await ApiService.fetchAllProducts(token);

            if (products.isNotEmpty) { // ✅ 데이터가 비어있지 않은지 확인
              try {
                productProvider.setProducts(List<Map<String, dynamic>>.from(products)); // ✅ 올바른 형 변환

                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("상품 목록이 업데이트되었습니다.")),
                );
              } catch (e) {
                print("❌ 상품 데이터 처리 오류: $e");
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("상품 데이터를 처리하는 중 오류가 발생했습니다.")),
                );
              }
            } else {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("업데이트 실패: 상품 목록이 비어 있습니다.")),
              );
            }

          },
        ),
        ElevatedButton.icon(
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
          ElevatedButton.icon(
            icon: const Icon(Icons.list),
            label: const Text("상품 조회"),
            onPressed: () {
            Navigator.push(
            context,
            MaterialPageRoute(
            builder: (_) => ProductScreen(token: token),
            ),
            );
          },
          ),
          ElevatedButton.icon(
            icon: const Icon(Icons.shopping_bag),
            label: const Text("주문 시작"),
            onPressed: () {
              _showDateSelectionDialog(context, token);
            },
          ),
          ElevatedButton.icon(
            icon: const Icon(Icons.history),
            label: const Text("주문 내역 조회"),
            onPressed: () {
              _showOrderDateSelectionDialog(context, token);
            },
          ),

          ElevatedButton.icon(
            icon: const Icon(Icons.business),
            label: const Text("거래처 관리"),
            onPressed: () {
              final auth = context.read<AuthProvider>(); // 현재 로그인한 직원 정보 가져오기

              if (auth.user == null) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("로그인이 필요합니다.")),
                );
                return;
              }

              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ClientsScreen(
                    token: auth.user!.token, // 현재 로그인한 직원의 토큰 전달
                    employeeId: auth.user!.id, // 현재 로그인한 직원의 ID 전달
                  ),
                ),
              );

            },
          ),


        ],
      ),

    );
  }
  void _showOrderDateSelectionDialog(BuildContext context, String token) {
    DateTime selectedDate = DateTime.now();

    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          title: const Text("주문 날짜 선택"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text("주문 내역을 조회할 날짜를 선택하세요."),
              SizedBox(height: 10),
              StatefulBuilder(
                builder: (context, setState) {
                  return Column(
                    children: [
                      CalendarDatePicker(
                        initialDate: selectedDate,
                        firstDate: DateTime.now().subtract(Duration(days: 365)),
                        lastDate: DateTime.now().add(Duration(days: 365)),
                        onDateChanged: (DateTime date) {
                          setState(() {
                            selectedDate = date;
                          });
                        },
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx); // 팝업 닫기
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => OrderHistoryScreen(token: token, selectedDate: selectedDate),
                  ),
                );
              },
              child: const Text("확인"),
            ),
          ],
        );
      },
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




  void _showDateSelectionDialog(BuildContext context, String token) {
    DateTime selectedDate = DateTime.now();

    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          title: const Text("주문 날짜 선택"),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text("주문할 날짜를 선택하세요."),
              SizedBox(height: 10),
              StatefulBuilder(
                builder: (context, setState) {
                  return Column(
                    children: [
                      CalendarDatePicker(
                        initialDate: selectedDate,
                        firstDate: DateTime.now().subtract(Duration(days: 365)),
                        lastDate: DateTime.now().add(Duration(days: 365)),
                        onDateChanged: (DateTime date) {
                          setState(() {
                            selectedDate = date;
                          });
                        },
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("취소"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx); // 팝업 닫기
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => OrderScreen(token: token, selectedDate: selectedDate),
                  ),
                );
              },
              child: const Text("확인"),
            ),
          ],
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
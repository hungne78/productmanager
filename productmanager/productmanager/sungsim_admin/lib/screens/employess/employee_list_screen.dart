// lib/screens/employees/employee_list_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/admin_api_service.dart';
import 'employee_detail_screen.dart';

class EmployeeListScreen extends StatefulWidget {
  const EmployeeListScreen({Key? key}) : super(key: key);

  @override
  _EmployeeListScreenState createState() => _EmployeeListScreenState();
}

class _EmployeeListScreenState extends State<EmployeeListScreen> {
  bool _isLoading = false;
  List<Map<String, dynamic>> _employees = [];

  @override
  void initState() {
    super.initState();
    _fetchEmployeesBasicInfo();
  }

  Future<void> _fetchEmployeesBasicInfo() async {
    setState(() => _isLoading = true);

    final auth = context.read<AuthProvider>();
    final token = auth.token;
    if (token == null) {
      setState(() => _isLoading = false);
      return;
    }

    try {
      // 예: GET /admin/employees/basic_info
      // 응답: [
      //   {
      //     "employee_id": 1,
      //     "name": "홍길동",
      //     "today_sales": 300000,
      //     "today_order_count": 12,
      //     "total_outstanding": 50000
      //   }, ...
      // ]
      final data = await AdminApiService.fetchEmployeesBasicInfo(token);
      setState(() {
        _employees = List<Map<String, dynamic>>.from(data);
      });
    } catch (e) {
      print("❌ 직원 목록 가져오기 실패: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("직원 목록 조회 실패: $e")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("직원 관리"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
        itemCount: _employees.length,
        itemBuilder: (_, i) {
          final emp = _employees[i];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
            child: ListTile(
              leading: CircleAvatar(child: Text(emp["employee_id"].toString())),
              title: Text(emp["name"] ?? "이름 없음"),
              subtitle: Text(
                "오늘 매출: ${emp["today_sales"]}원\n"
                    "오늘 주문: ${emp["today_order_count"]}건\n"
                    "총 미수금: ${emp["total_outstanding"]}원",
              ),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => EmployeeDetailScreen(employeeId: emp["employee_id"]),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

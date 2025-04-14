// lib/screens/clients/client_list_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/client_api_service.dart';
import 'client_detail_screen.dart';

class ClientListScreen extends StatefulWidget {
  const ClientListScreen({Key? key}) : super(key: key);

  @override
  _ClientListScreenState createState() => _ClientListScreenState();
}

class _ClientListScreenState extends State<ClientListScreen> {
  bool _isLoading = false;
  String? _error;

  // 직원별 거래처 구조
  // 예: [
  //   {
  //     "employee_id": 1,
  //     "employee_name": "홍길동",
  //     "clients": [
  //       { "client_id": 101, "client_name": "A상점", "region":"서울", "outstanding":30000, ... },
  //       ...
  //     ]
  //   }, ...
  // ]
  List<Map<String, dynamic>> _employeeClients = [];

  // 검색/필터
  final TextEditingController _searchController = TextEditingController();
  String? _regionFilter; // 지역 필터 (null=전체)
  // 예: ['전체','서울','경기','인천', ...] 라고 가정

  @override
  void initState() {
    super.initState();
    _fetchEmployeeClients();
  }

  Future<void> _fetchEmployeeClients() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _employeeClients.clear();
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
      // 서버에서 직원별로 거래처 목록을 한방에 가져오는 API 가정
      final data = await ClientApiService.fetchClientsByEmployee(token);
      // data: [
      //   {
      //     "employee_id":1,
      //     "employee_name":"홍길동",
      //     "clients":[ { "client_id":101,"client_name":"ABC유통", "region":"서울", "outstanding":10000 }, ...]
      //   },
      //   ...
      // ]
      setState(() => _employeeClients = data);
    } catch (e) {
      setState(() => _error = "직원/거래처 목록 조회 실패: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // 🔹 검색 적용
  // 필터 조건: 거래처명에 검색어 포함, region이 _regionFilter와 같거나 전체면 표시
  List<Map<String, dynamic>> _getFilteredEmployeeClients() {
    final searchText = _searchController.text.trim().toLowerCase();
    final region = _regionFilter == null || _regionFilter == "전체" ? null : _regionFilter;

    // 각 직원에 대해, clients 배열을 필터링
    List<Map<String, dynamic>> filtered = [];
    for (var emp in _employeeClients) {
      final empCopy = Map<String, dynamic>.from(emp);
      final allClients = List<Map<String, dynamic>>.from(emp["clients"] ?? []);
      final filteredClients = allClients.where((c) {
        final name = (c["client_name"] ?? "").toString().toLowerCase();
        final cRegion = c["region"] ?? "";
        if (searchText.isNotEmpty && !name.contains(searchText)) {
          return false; // 검색어 불일치
        }
        if (region != null && cRegion != region) {
          return false; // 지역 필터 불일치
        }
        return true;
      }).toList();

      if (filteredClients.isNotEmpty) {
        empCopy["clients"] = filteredClients;
        filtered.add(empCopy);
      }
    }
    return filtered;
  }

  @override
  Widget build(BuildContext context) {
    final filteredData = _getFilteredEmployeeClients();

    return Scaffold(
      appBar: AppBar(
        title: const Text("거래처 관리 (직원별)"),
      ),
      body: Column(
        children: [
          // (A) 검색/필터 영역
          _buildSearchBar(),

          // (B) 목록
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : filteredData.isEmpty
                ? const Center(child: Text("검색 결과 없음"))
                : _buildEmployeeClientView(filteredData),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      color: Colors.grey[200],
      child: Row(
        children: [
          // 검색어
          Expanded(
            flex: 2,
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                labelText: "거래처명 검색",
                border: OutlineInputBorder(),
              ),
              onChanged: (val) => setState(() {}), // 검색 실시간 반영
            ),
          ),
          const SizedBox(width: 8),

          // 지역 필터 (Dropdown 예시)
          Expanded(
            flex: 1,
            child: DropdownButtonFormField<String>(
              value: _regionFilter,
              items: <String?>["전체","서울","경기","인천","수원","안산","용인"].map((region) {
                return DropdownMenuItem(
                  value: region == "전체" ? "전체" : region,
                  child: Text(region ?? "전체"),
                );
              }).toList(),
              decoration: const InputDecoration(
                labelText: "지역",
                border: OutlineInputBorder(),
              ),
              onChanged: (val) {
                setState(() => _regionFilter = val == "전체" ? null : val);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmployeeClientView(List<Map<String, dynamic>> data) {
    // data = [
    //   {
    //     "employee_id":1,"employee_name":"홍길동",
    //     "clients":[{ "client_id":101,"client_name":"AAA",...}, ...]
    //   },...
    // ]
    return ListView.builder(
      itemCount: data.length,
      itemBuilder: (ctx, i) {
        final emp = data[i];
        final empName = emp["employee_name"] ?? "직원명 없음";
        final clients = List<Map<String, dynamic>>.from(emp["clients"] ?? []);

        return Card(
          margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
          child: ExpansionTile(
            title: Text("$empName (담당 거래처 ${clients.length}개)"),
            children: clients.map((c) {
              // c: { client_id, client_name, region, outstanding, ... }
              final clientId = c["client_id"];
              final clientName = c["client_name"];
              final region = c["region"] ?? "";
              final outstanding = c["outstanding"] ?? 0;

              return ListTile(
                leading: const Icon(Icons.storefront_outlined),
                title: Text("$clientName ($region)"),
                subtitle: Text("미수금: $outstanding 원"),
                onTap: () {
                  // 거래처 상세 화면 이동
                  Navigator.push(
                    ctx,
                    MaterialPageRoute(
                      builder: (_) => ClientDetailScreen(clientId: clientId),
                    ),
                  );
                },
              );
            }).toList(),
          ),
        );
      },
    );
  }
}

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ClientScreen extends StatefulWidget {
  final String token;
  const ClientScreen({Key? key, required this.token}) : super(key: key);

  @override
  State<ClientScreen> createState() => _ClientScreenState();
}

class _ClientScreenState extends State<ClientScreen> {
  bool _isLoading = false;
  String? _error;
  List<dynamic> _clients = [];

  @override
  void initState() {
    super.initState();
    _fetchClients();
  }

  Future<void> _fetchClients() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final url = Uri.parse("http://127.0.0.1:8000/clients");
      final resp = await http.get(url, headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer ${widget.token}",
      });
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as List;
        setState(() {
          _clients = data; // e.g. [{id:1, client_name:..., ...}, ...]
        });
      } else {
        setState(() => _error = "조회 실패: ${resp.statusCode}\n${resp.body}");
      }
    } catch (e) {
      setState(() => _error = "오류: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // 거래처 등록/수정 기능도 추가 가능

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("거래처 목록")),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(child: Text(_error!))
          : ListView.builder(
        itemCount: _clients.length,
        itemBuilder: (ctx, i) {
          final c = _clients[i];
          return ListTile(
            title: Text(c["client_name"] ?? "No Name"),
            subtitle: Text("Address: ${c["address"] ?? ""}"),
          );
        },
      ),
    );
  }
}

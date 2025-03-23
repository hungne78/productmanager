import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../auth_provider.dart';

class VehicleManagementScreen extends StatefulWidget {
  final String token;

  const VehicleManagementScreen({Key? key, required this.token}) : super(key: key);

  @override
  _VehicleManagementScreenState createState() => _VehicleManagementScreenState();
}

class _VehicleManagementScreenState extends State<VehicleManagementScreen> {
  late TextEditingController fuelCostController;
  late TextEditingController mileageController;
  late TextEditingController oilChangeController;
  bool _isLoading = true;
  Map<String, dynamic>? vehicleData;
  DateTime? selectedOilChangeDate;

  @override
  void initState() {
    super.initState();
    _fetchVehicleData();
    fuelCostController = TextEditingController();
    mileageController = TextEditingController();
    oilChangeController = TextEditingController();
  }

  Future<void> _fetchVehicleData() async {
    final authProvider = context.read<AuthProvider>();
    final int employeeId = authProvider.user?.id ?? 0;

    try {
      final response = await ApiService.getEmployeeVehicle(widget.token, employeeId);
      if (response.statusCode == 200) {
        setState(() {
          vehicleData = response.data;
          fuelCostController.text = vehicleData?['monthly_fuel_cost'].toString() ?? '';
          mileageController.text = vehicleData?['current_mileage'].toString() ?? '';

          String? lastOilChange = vehicleData?['last_engine_oil_change'];
          if (lastOilChange != null && lastOilChange.isNotEmpty) {
            selectedOilChangeDate = DateTime.parse(lastOilChange);
            oilChangeController.text = DateFormat('yyyy-MM-dd').format(selectedOilChangeDate!);
          }
        });
      }
    } catch (e) {
      print("🚨 차량 데이터 로딩 실패: $e");
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _updateVehicleData() async {
    if (vehicleData == null) {
      print("🚨 [Flutter] vehicleData가 null입니다. 업데이트를 중단합니다.");
      return;
    }

    final authProvider = context.read<AuthProvider>();
    final int employeeId = authProvider.user?.id ?? -1;

    if (!vehicleData!.containsKey("employee_id") || vehicleData!["employee_id"] == null) {
      print("🚨 [Flutter] vehicleData에 employee_id가 없습니다. vehicleData: $vehicleData");
      return;
    }

    final updatedData = {
      "monthly_fuel_cost": double.tryParse(fuelCostController.text) ?? 0,
      "current_mileage": int.tryParse(mileageController.text) ?? 0,
      "last_engine_oil_change": selectedOilChangeDate != null
          ? DateFormat('yyyy-MM-dd').format(selectedOilChangeDate!)
          : vehicleData?["last_engine_oil_change"],
    };

    try {
      final response = await ApiService.updateEmployeeVehicle(
        widget.token,
        vehicleData!['employee_id'],
        updatedData,
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("차량 정보가 업데이트되었습니다!"),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      print("🚨 [Flutter] 차량 업데이트 실패: $e");
    }
  }

  Future<void> _selectOilChangeDate(BuildContext context) async {
    DateTime? pickedDate = await showDatePicker(
      context: context,
      initialDate: selectedOilChangeDate ?? DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );

    if (pickedDate != null) {
      setState(() {
        selectedOilChangeDate = pickedDate;
        oilChangeController.text = DateFormat('yyyy-MM-dd').format(pickedDate);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        backgroundColor: Colors.indigo,
        elevation: 2,
        automaticallyImplyLeading: false,
        leading: IconButton(
          icon: Icon(Icons.home, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Center(
          child: Text("차량 관리", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
        actions: [SizedBox(width: 48)], // 중앙 정렬 맞춤
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            _buildCardField("월 연료비 (원)", fuelCostController, Icons.local_gas_station),
            _buildCardField("현재 주행 거리 (km)", mileageController, Icons.speed),
            GestureDetector(
              onTap: () => _selectOilChangeDate(context),
              child: AbsorbPointer(
                child: _buildCardField("최근 엔진오일 교환 날짜", oilChangeController, Icons.calendar_today),
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _updateVehicleData,
                icon: Icon(Icons.save, color: Colors.white),
                label: Text("차량 정보 업데이트", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.indigo,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildCardField(String label, TextEditingController controller, IconData icon) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 10),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8),
        child: TextField(
          controller: controller,
          keyboardType: label.contains("거리") || label.contains("연료비") ? TextInputType.number : TextInputType.text,
          decoration: InputDecoration(
            labelText: label,
            prefixIcon: Icon(icon, color: Colors.indigo),
            border: InputBorder.none,
          ),
        ),
      ),
    );
  }


  Widget _buildInputField(String label, TextEditingController controller, IconData icon) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10.0),
      child: TextField(
        controller: controller,
        keyboardType: label.contains("거리") ? TextInputType.number : TextInputType.text,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: Colors.deepPurple),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          filled: true,
          fillColor: Colors.grey[100],
          focusedBorder: OutlineInputBorder(
            borderSide: BorderSide(color: Colors.deepPurple, width: 2),
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    fuelCostController.dispose();
    mileageController.dispose();
    oilChangeController.dispose();
    super.dispose();
  }
}

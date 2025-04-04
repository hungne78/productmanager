// location_service.dart
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';

class LocationService {
  /// 주어진 주소(address)를 좌표로 변환 후,
  /// 현재 기기 위치와의 거리를 계산하여 반환 (미터).
  /// 주소를 찾을 수 없으면 null 을 반환.
  static Future<double?> distanceFromCurrentPosition(String address) async {
    try {
      // 1) 현재 기기 위치 확인
      Position myPosition = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      // 2) 주소 → 좌표(위도경도) 변환
      List<Location> locations = await locationFromAddress(address);
      if (locations.isEmpty) return null; // 주소 좌표를 못 찾은 경우

      final target = locations.first;
      double distanceInMeters = Geolocator.distanceBetween(
        myPosition.latitude,
        myPosition.longitude,
        target.latitude,
        target.longitude,
      );
      return distanceInMeters;
    } catch (e) {
      // 주소를 찾지 못하거나, 위치 권한 오류 등 발생 시
      return null;
    }
  }
}

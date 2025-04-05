class User {
  final int id;
  final String name;
  final String? phone;
  final String role;  // 🔹 role 필드 추가
  final String token; // 🔹 token 필드 추가

  User({
    required this.id,
    required this.name,
    this.phone,
    required this.role,  // 🔹 필수 값으로 설정
    required this.token, // 🔹 필수 값으로 설정
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json["id"],
      name: json["name"],
      phone: json["phone"],
      role: json["role"],   // 🔹 role 받아오기
      token: json["token"], // 🔹 token 받아오기
    );
  }
}

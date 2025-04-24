// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'baseline.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class BaselineAdapter extends TypeAdapter<Baseline> {
  @override
  final int typeId = 0;

  @override
  Baseline read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return Baseline(
      fields[0] as double,
      fields[1] as double,
    );
  }

  @override
  void write(BinaryWriter writer, Baseline obj) {
    writer
      ..writeByte(2)
      ..writeByte(0)
      ..write(obj.shoulder)
      ..writeByte(1)
      ..write(obj.hip);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is BaselineAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

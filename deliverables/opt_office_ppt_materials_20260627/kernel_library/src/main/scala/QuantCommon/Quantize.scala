package QuantCommon

import QuantCommon.Pack._
import QuantCommon.Precision._
import chisel3._

// INT8 pack -> FP32 pack, x_fp32 = x_int8 * scale
class Int8DequantizePack extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(INT8_PACK_WIDTH.W))
    val scale = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_PACK_WIDTH.W))
  })

  val inVec = asInt8Vec(io.in)
  val outVec = Wire(Vec(LANES, UInt(FP32_WIDTH.W)))

  for (i <- 0 until LANES) {
    val toFp = Module(new Int8ToFp32)
    val mul = Module(new Fp32Mul)
    toFp.io.in := inVec(i).asSInt
    mul.io.a := toFp.io.out
    mul.io.b := io.scale
    outVec(i) := mul.io.out
  }

  io.out := outVec.asUInt
}

// UINT8 pack -> FP32 pack, x_fp32 = (x_u8 - zp) * scale
class UInt8DequantizePack extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(INT8_PACK_WIDTH.W))
    val zeroPoint = Input(UInt(UINT8_WIDTH.W))
    val scale = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_PACK_WIDTH.W))
  })

  val inVec = asUInt8Vec(io.in)
  val outVec = Wire(Vec(LANES, UInt(FP32_WIDTH.W)))

  for (i <- 0 until LANES) {
    val diff = Wire(SInt((UINT8_WIDTH + 1).W))
    diff := inVec(i).zext - io.zeroPoint.zext

    val toFp = Module(new SIntToFp32(UINT8_WIDTH + 1))
    val mul = Module(new Fp32Mul)
    toFp.io.in := diff
    mul.io.a := toFp.io.out
    mul.io.b := io.scale
    outVec(i) := mul.io.out
  }

  io.out := outVec.asUInt
}

// FP32 pack -> INT8 pack, q = round(x * invScale + zp)
class Fp32QuantizeToInt8Pack extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(FP32_PACK_WIDTH.W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val zeroPoint = Input(SInt(INT8_WIDTH.W))
    val out = Output(UInt(INT8_PACK_WIDTH.W))
  })

  val inVec = asFp32Vec(io.in)
  val outVec = Wire(Vec(LANES, UInt(INT8_WIDTH.W)))
  val zpFp = Module(new SIntToFp32(INT8_WIDTH))
  zpFp.io.in := io.zeroPoint

  for (i <- 0 until LANES) {
    val mul = Module(new Fp32Mul)
    val add = Module(new Fp32Add)
    val toInt = Module(new Fp32ToInt8)

    mul.io.a := inVec(i)
    mul.io.b := io.invScale
    add.io.a := mul.io.out
    add.io.b := zpFp.io.out
    toInt.io.in := add.io.out

    outVec(i) := toInt.io.out
  }

  io.out := outVec.asUInt
}

// FP32 pack -> UINT8 pack, q = round(x * invScale + zp)
class Fp32QuantizeToUInt8Pack extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(FP32_PACK_WIDTH.W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val zeroPoint = Input(UInt(UINT8_WIDTH.W))
    val out = Output(UInt(INT8_PACK_WIDTH.W))
  })

  val inVec = asFp32Vec(io.in)
  val outVec = Wire(Vec(LANES, UInt(UINT8_WIDTH.W)))
  val zpFp = Module(new UInt8ToFp32)
  zpFp.io.in := io.zeroPoint

  for (i <- 0 until LANES) {
    val mul = Module(new Fp32Mul)
    val add = Module(new Fp32Add)
    val toInt = Module(new Fp32ToUInt8)

    mul.io.a := inVec(i)
    mul.io.b := io.invScale
    add.io.a := mul.io.out
    add.io.b := zpFp.io.out
    toInt.io.in := add.io.out

    outVec(i) := toInt.io.out
  }

  io.out := outVec.asUInt
}

class Fp32QuantizeToInt8Vec(val lanes: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt((lanes * FP32_WIDTH).W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val zeroPoint = Input(SInt(INT8_WIDTH.W))
    val out = Output(UInt((lanes * INT8_WIDTH).W))
  })

  val inVec = io.in.asTypeOf(Vec(lanes, UInt(FP32_WIDTH.W)))
  val outVec = Wire(Vec(lanes, UInt(INT8_WIDTH.W)))
  val zpFp = Module(new SIntToFp32(INT8_WIDTH))
  zpFp.io.in := io.zeroPoint

  for (i <- 0 until lanes) {
    val mul = Module(new Fp32Mul)
    val add = Module(new Fp32Add)
    val toInt = Module(new Fp32ToInt8)

    mul.io.a := inVec(i)
    mul.io.b := io.invScale
    add.io.a := mul.io.out
    add.io.b := zpFp.io.out
    toInt.io.in := add.io.out
    outVec(i) := toInt.io.out
  }

  io.out := outVec.asUInt
}

class Fp32QuantizeToUInt8Vec(val lanes: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt((lanes * FP32_WIDTH).W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val zeroPoint = Input(UInt(UINT8_WIDTH.W))
    val out = Output(UInt((lanes * UINT8_WIDTH).W))
  })

  val inVec = io.in.asTypeOf(Vec(lanes, UInt(FP32_WIDTH.W)))
  val outVec = Wire(Vec(lanes, UInt(UINT8_WIDTH.W)))
  val zpFp = Module(new UInt8ToFp32)
  zpFp.io.in := io.zeroPoint

  for (i <- 0 until lanes) {
    val mul = Module(new Fp32Mul)
    val add = Module(new Fp32Add)
    val toInt = Module(new Fp32ToUInt8)

    mul.io.a := inVec(i)
    mul.io.b := io.invScale
    add.io.a := mul.io.out
    add.io.b := zpFp.io.out
    toInt.io.in := add.io.out
    outVec(i) := toInt.io.out
  }

  io.out := outVec.asUInt
}

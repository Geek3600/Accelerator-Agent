package QuantCommon

import QuantCommon.Precision._
import QuantCommon.Pack._
import chisel3._

// 12-lane int32 累加结果 -> FP32 输出
// 公式: y_fp32 = acc_int32 * scale + bias_fp32
class Int32AccToFp32Pack extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(FP32_PACK_WIDTH.W))
    val scale = Input(UInt(FP32_WIDTH.W))
    val bias = Input(UInt(FP32_PACK_WIDTH.W))
    val out = Output(UInt(FP32_PACK_WIDTH.W))
  })

  val inVec = io.in.asTypeOf(Vec(LANES, SInt(INT32_WIDTH.W)))
  val biasVec = asFp32Vec(io.bias)
  val outVec = Wire(Vec(LANES, UInt(FP32_WIDTH.W)))

  for (i <- 0 until LANES) {
    val toFp = Module(new Int32ToFp32)
    val mul = Module(new Fp32Mul)
    val add = Module(new Fp32Add)

    toFp.io.in := inVec(i)
    mul.io.a := toFp.io.out
    mul.io.b := io.scale
    add.io.a := mul.io.out
    add.io.b := biasVec(i)

    outVec(i) := add.io.out
  }

  io.out := outVec.asUInt
}

// 通用 int32 向量 -> FP32 向量
// 公式: y_fp32 = acc_int32 * scale
class Int32VecToFp32(val lanes: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt((lanes * INT32_WIDTH).W))
    val scale = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt((lanes * FP32_WIDTH).W))
  })

  val inVec = io.in.asTypeOf(Vec(lanes, SInt(INT32_WIDTH.W)))
  val outVec = Wire(Vec(lanes, UInt(FP32_WIDTH.W)))

  for (i <- 0 until lanes) {
    val toFp = Module(new Int32ToFp32)
    val mul = Module(new Fp32Mul)

    toFp.io.in := inVec(i)
    mul.io.a := toFp.io.out
    mul.io.b := io.scale
    outVec(i) := mul.io.out
  }

  io.out := outVec.asUInt
}

class Int32VecRequantizeToInt8(val lanes: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt((lanes * INT32_WIDTH).W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt((lanes * INT8_WIDTH).W))
  })

  val inVec = io.in.asTypeOf(Vec(lanes, SInt(INT32_WIDTH.W)))
  val outVec = Wire(Vec(lanes, UInt(INT8_WIDTH.W)))

  for (i <- 0 until lanes) {
    val toFp = Module(new Int32ToFp32)
    val mul = Module(new Fp32Mul)
    val toInt = Module(new Fp32ToInt8)

    toFp.io.in := inVec(i)
    mul.io.a := toFp.io.out
    mul.io.b := io.invScale
    toInt.io.in := mul.io.out
    outVec(i) := toInt.io.out
  }

  io.out := outVec.asUInt
}

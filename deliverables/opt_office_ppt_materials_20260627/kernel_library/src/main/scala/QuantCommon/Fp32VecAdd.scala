package QuantCommon

import QuantCommon.Precision._
import QuantCommon.Pack._
import chisel3._

// 12-lane FP32 向量加法
// 用于后续 ResAdd / ResAdd2 在浮点域完成残差相加
class Fp32VecAdd extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_PACK_WIDTH.W))
    val b = Input(UInt(FP32_PACK_WIDTH.W))
    val out = Output(UInt(FP32_PACK_WIDTH.W))
    val exceptionFlags = Output(Vec(LANES, UInt(5.W)))
  })

  val aVec = asFp32Vec(io.a)
  val bVec = asFp32Vec(io.b)
  val outVec = Wire(Vec(LANES, UInt(FP32_WIDTH.W)))
  val flags = Wire(Vec(LANES, UInt(5.W)))

  for (i <- 0 until LANES) {
    val add = Module(new Fp32Add)
    add.io.a := aVec(i)
    add.io.b := bVec(i)
    outVec(i) := add.io.out
    flags(i) := add.io.exceptionFlags
  }

  io.out := outVec.asUInt
  io.exceptionFlags := flags
}

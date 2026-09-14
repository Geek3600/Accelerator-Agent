package QKVLinear

import QKVLinear.Param.DATAW
import QuantCommon.{Fp32Add, Fp32AddComb, Fp32Mul, Fp32MulComb, Fp32ToSInt, Fp32ToSIntComb, FpBackend, Int32ToFp32, Int32ToFp32Comb, Int8ToFp32, Int8ToFp32Comb}
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class PipReg(val depth: Int, val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(width.W))
    val out = Output(UInt(width.W))
  })
  val pipData = Wire(Vec(depth + 1, UInt(width.W)))
  for (i <- 0 until depth) {
    pipData(i + 1) := RegNext(pipData(i))
  }
  pipData(0) := io.in
  io.out := pipData(depth)
}

class Multiplier extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(UInt(DATAW.W))
    val in1 = Input(UInt(DATAW.W))
    val out = Output(UInt(DATAW.W))
  })
  io.out := RegNext(io.in0 * io.in1)
}

class AddTree(val num: Int) extends Module {
  val io = IO(new Bundle() {
    val ins = Input(Vec(num, UInt(DATAW.W)))
    val out = Output(UInt(DATAW.W))
  })

  def recFNAddTree(vals: Seq[UInt]): UInt = {
    if (vals.length == 1) vals.head
    else {
      val next = vals.grouped(2).map {
        case Seq(a, b) => RegNext(a + b)
        case Seq(a) => RegNext(a)
      }.toSeq
      recFNAddTree(next)
    }
  }
  io.out := recFNAddTree(io.ins)
}

class Int32VecScaleToSInt32(val lanes: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt((lanes * INT32_WIDTH).W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt((lanes * INT32_WIDTH).W))
  })

  val inVec = io.in.asTypeOf(Vec(lanes, SInt(INT32_WIDTH.W)))
  val outVec = Wire(Vec(lanes, UInt(INT32_WIDTH.W)))

  for (i <- 0 until lanes) {
    if (FpBackend.useVivadoIp) {
      val toFp = Module(new Int32ToFp32)
      val mul = Module(new Fp32Mul)
      val toInt = Module(new Fp32ToSInt(INT32_WIDTH))

      toFp.io.in := inVec(i)
      mul.io.a := toFp.io.out
      mul.io.b := io.invScale
      toInt.io.in := mul.io.out
      outVec(i) := toInt.io.out
    } else {
      val toFp = Module(new Int32ToFp32Comb)
      val mul = Module(new Fp32MulComb)
      val toInt = Module(new Fp32ToSIntComb(INT32_WIDTH))

      toFp.io.in := inVec(i)
      mul.io.a := toFp.io.out
      mul.io.b := io.invScale
      toInt.io.in := mul.io.out
      outVec(i) := toInt.io.out
    }
  }

  io.out := outVec.asUInt
}

class Int32VecScaleBiasToSInt32(val lanes: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt((lanes * INT32_WIDTH).W))
    val accScale = Input(UInt(FP32_WIDTH.W))
    val bias = Input(UInt((lanes * DATAW).W))
    val biasScale = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt((lanes * INT32_WIDTH).W))
  })

  val inVec = io.in.asTypeOf(Vec(lanes, SInt(INT32_WIDTH.W)))
  val biasVec = io.bias.asTypeOf(Vec(lanes, SInt(DATAW.W)))
  val outVec = Wire(Vec(lanes, UInt(INT32_WIDTH.W)))

  for (i <- 0 until lanes) {
    if (FpBackend.useVivadoIp) {
      val accToFp = Module(new Int32ToFp32)
      val accMul = Module(new Fp32Mul)
      val biasToFp = Module(new Int8ToFp32)
      val biasMul = Module(new Fp32Mul)
      val add = Module(new Fp32Add)
      val toInt = Module(new Fp32ToSInt(INT32_WIDTH))

      accToFp.io.in := inVec(i)
      accMul.io.a := accToFp.io.out
      accMul.io.b := io.accScale

      biasToFp.io.in := biasVec(i)
      biasMul.io.a := biasToFp.io.out
      biasMul.io.b := io.biasScale

      add.io.a := accMul.io.out
      add.io.b := biasMul.io.out

      toInt.io.in := add.io.out
      outVec(i) := toInt.io.out
    } else {
      val accToFp = Module(new Int32ToFp32Comb)
      val accMul = Module(new Fp32MulComb)
      val biasToFp = Module(new Int8ToFp32Comb)
      val biasMul = Module(new Fp32MulComb)
      val add = Module(new Fp32AddComb)
      val toInt = Module(new Fp32ToSIntComb(INT32_WIDTH))

      accToFp.io.in := inVec(i)
      accMul.io.a := accToFp.io.out
      accMul.io.b := io.accScale

      biasToFp.io.in := biasVec(i)
      biasMul.io.a := biasToFp.io.out
      biasMul.io.b := io.biasScale

      add.io.a := accMul.io.out
      add.io.b := biasMul.io.out

      toInt.io.in := add.io.out
      outVec(i) := toInt.io.out
    }
  }

  io.out := outVec.asUInt
}

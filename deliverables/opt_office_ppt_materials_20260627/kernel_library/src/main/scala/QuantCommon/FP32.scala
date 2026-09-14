package QuantCommon

import QuantCommon.Precision._
import chisel3._
import hardfloat._

class Fp32Add extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val add = Module(new XilinxFpAddCompat)
  val aValid = WireDefault(true.B)
  val bValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(aValid)
  dontTouch(bValid)
  dontTouch(outReady)
  add.aclk := clock
  add.s_axis_a_tvalid := aValid
  add.s_axis_a_tdata := io.a
  add.s_axis_b_tvalid := bValid
  add.s_axis_b_tdata := io.b
  add.m_axis_result_tready := outReady

  io.out := add.m_axis_result_tdata
  io.exceptionFlags := 0.U
}

class Fp32AddComb extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val add = Module(new AddRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  add.io.subOp := false.B
  add.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  add.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  add.io.roundingMode := ROUNDING_MODE
  add.io.detectTininess := DETECT_TININESS

  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, add.io.out)
  io.exceptionFlags := add.io.exceptionFlags
}

class Fp32Sub extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val sub = Module(new XilinxFpAddCompat(true))
  val aValid = WireDefault(true.B)
  val bValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(aValid)
  dontTouch(bValid)
  dontTouch(outReady)
  sub.aclk := clock
  sub.s_axis_a_tvalid := aValid
  sub.s_axis_a_tdata := io.a
  sub.s_axis_b_tvalid := bValid
  sub.s_axis_b_tdata := io.b
  sub.m_axis_result_tready := outReady

  io.out := sub.m_axis_result_tdata
  io.exceptionFlags := 0.U
}

class Fp32Mul extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val mul = Module(new XilinxFpMulCompat)
  val aValid = WireDefault(true.B)
  val bValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(aValid)
  dontTouch(bValid)
  dontTouch(outReady)
  mul.aclk := clock
  mul.s_axis_a_tvalid := aValid
  mul.s_axis_a_tdata := io.a
  mul.s_axis_b_tvalid := bValid
  mul.s_axis_b_tdata := io.b
  mul.m_axis_result_tready := outReady

  io.out := mul.m_axis_result_tdata
  io.exceptionFlags := 0.U
}

class Fp32MulComb extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val mul = Module(new MulRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  mul.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  mul.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  mul.io.roundingMode := ROUNDING_MODE
  mul.io.detectTininess := DETECT_TININESS.asBool

  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, mul.io.out)
  io.exceptionFlags := mul.io.exceptionFlags
}

class Fp32MulAdd extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val c = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val mulAdd = Module(new MulAddRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  mulAdd.io.op := 0.U
  mulAdd.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  mulAdd.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  mulAdd.io.c := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.c)
  mulAdd.io.roundingMode := ROUNDING_MODE
  mulAdd.io.detectTininess := DETECT_TININESS

  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, mulAdd.io.out)
  io.exceptionFlags := mulAdd.io.exceptionFlags
}

class Fp32Compare extends Module {
  val io = IO(new Bundle() {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val lt = Output(Bool())
    val eq = Output(Bool())
    val gt = Output(Bool())
    val exceptionFlags = Output(UInt(5.W))
  })

  val lt = Module(new XilinxFpCompareCompat("lt"))
  val eq = Module(new XilinxFpCompareCompat("eq"))
  val gt = Module(new XilinxFpCompareCompat("gt"))
  val aValid = WireDefault(true.B)
  val bValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(aValid)
  dontTouch(bValid)
  dontTouch(outReady)

  for (cmp <- Seq(lt, eq, gt)) {
    cmp.aclk := clock
    cmp.s_axis_a_tvalid := aValid
    cmp.s_axis_a_tdata := io.a
    cmp.s_axis_b_tvalid := bValid
    cmp.s_axis_b_tdata := io.b
    cmp.m_axis_result_tready := outReady
  }

  io.lt := lt.m_axis_result_tdata(0)
  io.eq := eq.m_axis_result_tdata(0)
  io.gt := gt.m_axis_result_tdata(0)
  io.exceptionFlags := 0.U
}

class SIntToFp32(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(SInt(intWidth.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val cvt = Module(new XilinxFpIntToFloatCompat(intWidth, signedIn = true))
  val inValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(inValid)
  dontTouch(outReady)
  cvt.aclk := clock
  cvt.s_axis_a_tvalid := inValid
  cvt.s_axis_a_tdata := io.in.asUInt
  cvt.m_axis_result_tready := outReady

  io.out := cvt.m_axis_result_tdata
  io.exceptionFlags := 0.U
}

class UIntToFp32(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(intWidth.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val cvt = Module(new XilinxFpIntToFloatCompat(intWidth, signedIn = false))
  val inValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(inValid)
  dontTouch(outReady)
  cvt.aclk := clock
  cvt.s_axis_a_tvalid := inValid
  cvt.s_axis_a_tdata := io.in
  cvt.m_axis_result_tready := outReady

  io.out := cvt.m_axis_result_tdata
  io.exceptionFlags := 0.U
}

class UIntToFp32Comb(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(intWidth.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val cvt = Module(new INToRecFN(intWidth, FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  cvt.io.signedIn := false.B
  cvt.io.in := io.in
  cvt.io.roundingMode := ROUNDING_MODE
  cvt.io.detectTininess := DETECT_TININESS

  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, cvt.io.out)
  io.exceptionFlags := 0.U
}

class SIntToFp32Comb(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(SInt(intWidth.W))
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val cvt = Module(new INToRecFN(intWidth, FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  cvt.io.signedIn := true.B
  cvt.io.in := io.in.asUInt
  cvt.io.roundingMode := ROUNDING_MODE
  cvt.io.detectTininess := DETECT_TININESS

  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, cvt.io.out)
  io.exceptionFlags := 0.U
}

class Fp32ToSInt(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(intWidth.W))
    val intExceptionFlags = Output(UInt(3.W))
  })

  val cvt = Module(new XilinxFpFloatToIntCompat(intWidth, signedOut = true))
  val inValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(inValid)
  dontTouch(outReady)
  cvt.aclk := clock
  cvt.s_axis_a_tvalid := inValid
  cvt.s_axis_a_tdata := io.in
  cvt.m_axis_result_tready := outReady

  io.out := cvt.m_axis_result_tdata
  io.intExceptionFlags := 0.U
}

class Fp32ToSIntComb(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(intWidth.W))
    val intExceptionFlags = Output(UInt(3.W))
  })

  val cvt = Module(new RecFNToIN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, intWidth))
  cvt.io.in := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.in)
  cvt.io.roundingMode := ROUNDING_MODE
  cvt.io.signedOut := true.B

  io.out := cvt.io.out
  io.intExceptionFlags := 0.U
}

class Fp32ToUInt(val intWidth: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(intWidth.W))
    val intExceptionFlags = Output(UInt(3.W))
  })

  val cvt = Module(new XilinxFpFloatToIntCompat(intWidth, signedOut = false))
  val inValid = WireDefault(true.B)
  val outReady = WireDefault(true.B)
  dontTouch(inValid)
  dontTouch(outReady)
  cvt.aclk := clock
  cvt.s_axis_a_tvalid := inValid
  cvt.s_axis_a_tdata := io.in
  cvt.m_axis_result_tready := outReady

  io.out := cvt.m_axis_result_tdata
  io.intExceptionFlags := 0.U
}

class Fp32DivSqrt extends Module {
  val io = IO(new Bundle() {
    val inValid = Input(Bool())
    val sqrtOp = Input(Bool())
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val inReady = Output(Bool())
    val outValidDiv = Output(Bool())
    val outValidSqrt = Output(Bool())
    val out = Output(UInt(FP32_WIDTH.W))
    val exceptionFlags = Output(UInt(5.W))
  })

  val div = Module(new XilinxFpDivCompat)
  val sqrt = Module(new XilinxFpSqrtCompat)

  div.aclk := clock
  div.s_axis_a_tvalid := io.inValid && !io.sqrtOp
  div.s_axis_a_tdata := io.a
  div.s_axis_b_tvalid := io.inValid && !io.sqrtOp
  div.s_axis_b_tdata := io.b
  div.m_axis_result_tready := true.B

  sqrt.aclk := clock
  sqrt.s_axis_a_tvalid := io.inValid && io.sqrtOp
  sqrt.s_axis_a_tdata := io.a
  sqrt.m_axis_result_tready := true.B

  io.inReady := Mux(io.sqrtOp, sqrt.s_axis_a_tready, div.s_axis_a_tready && div.s_axis_b_tready)
  io.outValidDiv := div.m_axis_result_tvalid
  io.outValidSqrt := sqrt.m_axis_result_tvalid
  io.out := Mux(sqrt.m_axis_result_tvalid, sqrt.m_axis_result_tdata, div.m_axis_result_tdata)
  io.exceptionFlags := 0.U
}

class Int8ToFp32 extends SIntToFp32(INT8_WIDTH)
class Int8ToFp32Comb extends SIntToFp32Comb(INT8_WIDTH)
class UInt8ToFp32 extends UIntToFp32(UINT8_WIDTH)
class Int32ToFp32 extends SIntToFp32(INT32_WIDTH)
class Int32ToFp32Comb extends SIntToFp32Comb(INT32_WIDTH)
class Fp32ToInt8 extends Fp32ToSInt(INT8_WIDTH)
class Fp32ToUInt8 extends Fp32ToUInt(UINT8_WIDTH)

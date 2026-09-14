package QuantCommon

import QuantCommon.Precision._
import chisel3._
import chisel3.experimental.ExtModule
import chisel3.util.{Cat, ShiftRegister}
import hardfloat._

object XilinxFpTargetConfig {
  // Vivado 2021.1 floating_point IP, single precision, Speed_Optimized,
  // Maximum_Latency=true, Flow_Control=Blocking
  val AddLatency = 12
  val MulLatency = 9
  val DivLatency = 29
  val SqrtLatency = 29
  val CompareLatency = 3
  val FixedToFloatLatency = 7
  val FloatToFixedLatency = 7

  // HardFloat DivSqrtRecFN_small uses sigWidth + 3 cycles for FP32.
  val HardFloatDivSqrtLatency = FP32_SIG_WIDTH + 3
  val DivSqrtPadLatency = DivLatency - HardFloatDivSqrtLatency
}

private object XilinxFpCompatUtil {
  def keep[T <: Data](x: T): T = {
    dontTouch(x)
    x
  }

  def axisByteWidth(bits: Int): Int = ((bits + 7) / 8) * 8

  def delayValid(in: Bool, stages: Int): Bool = {
    if (stages == 0) in
    else {
      val regs = RegInit(VecInit(Seq.fill(stages)(false.B)))
      regs(0) := in
      for (i <- 1 until stages) {
        regs(i) := regs(i - 1)
      }
      regs(stages - 1)
    }
  }
}

private object XilinxFpIpName {
  def add(subOp: Boolean): String = if (subOp) "fp_sub_sp_12" else "fp_add_sp_12"
  val mul = "fp_mul_sp_9"
  def compare(kind: String): String = s"fp_cmp_${kind}_sp_3"
  def intToFloat(intWidth: Int, signedIn: Boolean): String =
    s"fp_i2f_${if (signedIn) "s" else "u"}${intWidth}_sp_7"
  def floatToInt(intWidth: Int, signedOut: Boolean): String =
    s"fp_f2i_${if (signedOut) "s" else "u"}${intWidth}_sp_7"
  val div = "fp_div_sp_29"
  val sqrt = "fp_sqrt_sp_29"
}

private class VivadoFpBinaryIp(moduleName: String, resultWidth: Int = FP32_WIDTH) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(FP32_WIDTH.W)))
  val s_axis_b_tvalid = IO(Input(Bool()))
  val s_axis_b_tready = IO(Output(Bool()))
  val s_axis_b_tdata = IO(Input(UInt(FP32_WIDTH.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tready = IO(Input(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(resultWidth.W)))
}

private class VivadoFpBinaryIpNoResultReady(moduleName: String, resultWidth: Int = FP32_WIDTH) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(FP32_WIDTH.W)))
  val s_axis_b_tvalid = IO(Input(Bool()))
  val s_axis_b_tready = IO(Output(Bool()))
  val s_axis_b_tdata = IO(Input(UInt(FP32_WIDTH.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(resultWidth.W)))
}

private class VivadoFpUnaryIp(moduleName: String, inWidth: Int, resultWidth: Int) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(inWidth.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tready = IO(Input(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(resultWidth.W)))
}

private class VivadoFpUnaryIpNoResultReady(moduleName: String, inWidth: Int, resultWidth: Int) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(inWidth.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(resultWidth.W)))
}

private class HardFloatAddCore(val subOpValue: Boolean) extends Module {
  val io = IO(new Bundle {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
  })

  val add = Module(new AddRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  add.io.subOp := subOpValue.B
  add.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  add.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  add.io.roundingMode := ROUNDING_MODE
  add.io.detectTininess := DETECT_TININESS.asBool
  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, add.io.out)
}

private class HardFloatMulCore extends Module {
  val io = IO(new Bundle {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
  })

  val mul = Module(new MulRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  mul.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  mul.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  mul.io.roundingMode := ROUNDING_MODE
  mul.io.detectTininess := DETECT_TININESS.asBool
  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, mul.io.out)
}

private class HardFloatCompareCore extends Module {
  val io = IO(new Bundle {
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val lt = Output(Bool())
    val eq = Output(Bool())
    val gt = Output(Bool())
  })

  val cmp = Module(new CompareRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  cmp.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  cmp.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  cmp.io.signaling := false.B
  io.lt := cmp.io.lt
  io.eq := cmp.io.eq
  io.gt := cmp.io.gt
}

private class HardFloatIntToFpCore(val intWidth: Int, val signedIn: Boolean) extends Module {
  val io = IO(new Bundle {
    val in = Input(UInt(intWidth.W))
    val out = Output(UInt(FP32_WIDTH.W))
  })

  val cvt = Module(new INToRecFN(intWidth, FP32_EXP_WIDTH, FP32_SIG_WIDTH))
  cvt.io.signedIn := signedIn.B
  cvt.io.in := io.in
  cvt.io.roundingMode := ROUNDING_MODE
  cvt.io.detectTininess := DETECT_TININESS
  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, cvt.io.out)
}

private class HardFloatFpToIntCore(val intWidth: Int, val signedOut: Boolean) extends Module {
  val io = IO(new Bundle {
    val in = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(intWidth.W))
  })

  val cvt = Module(new RecFNToIN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, intWidth))
  cvt.io.in := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.in)
  cvt.io.roundingMode := ROUNDING_MODE
  cvt.io.signedOut := signedOut.B
  io.out := cvt.io.out
}

private class HardFloatDivSqrtCore(val sqrtOpValue: Boolean) extends Module {
  val io = IO(new Bundle {
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val a = Input(UInt(FP32_WIDTH.W))
    val b = Input(UInt(FP32_WIDTH.W))
    val outValid = Output(Bool())
    val out = Output(UInt(FP32_WIDTH.W))
  })

  val divSqrt = Module(new DivSqrtRecFN_small(FP32_EXP_WIDTH, FP32_SIG_WIDTH, 0))
  divSqrt.io.inValid := io.inValid
  divSqrt.io.sqrtOp := sqrtOpValue.B
  divSqrt.io.a := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.a)
  divSqrt.io.b := recFNFromFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, io.b)
  divSqrt.io.roundingMode := ROUNDING_MODE
  divSqrt.io.detectTininess := DETECT_TININESS
  io.inReady := divSqrt.io.inReady
  io.outValid := Mux(sqrtOpValue.B, divSqrt.io.outValid_sqrt, divSqrt.io.outValid_div)
  io.out := fNFromRecFN(FP32_EXP_WIDTH, FP32_SIG_WIDTH, divSqrt.io.out)
}

class XilinxFpAddCompat(val subOp: Boolean = false) extends Module {
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val s_axis_b_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_b_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_b_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(FP32_WIDTH.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpBinaryIpNoResultReady(XilinxFpIpName.add(subOp)))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := s_axis_a_tdata
    ip.s_axis_b_tvalid := s_axis_b_tvalid
    ip.s_axis_b_tdata := s_axis_b_tdata
    s_axis_a_tready := ip.s_axis_a_tready
    s_axis_b_tready := ip.s_axis_b_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatAddCore(subOp))
      val inFire = s_axis_a_tvalid && s_axis_b_tvalid
      core.io.a := s_axis_a_tdata
      core.io.b := s_axis_b_tdata
      s_axis_a_tready := true.B
      s_axis_b_tready := true.B
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(inFire, XilinxFpTargetConfig.AddLatency)
      m_axis_result_tdata := ShiftRegister(core.io.out, XilinxFpTargetConfig.AddLatency)
    }
  }
}

class XilinxFpMulCompat extends Module {
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val s_axis_b_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_b_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_b_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(FP32_WIDTH.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpBinaryIpNoResultReady(XilinxFpIpName.mul))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := s_axis_a_tdata
    ip.s_axis_b_tvalid := s_axis_b_tvalid
    ip.s_axis_b_tdata := s_axis_b_tdata
    s_axis_a_tready := ip.s_axis_a_tready
    s_axis_b_tready := ip.s_axis_b_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatMulCore)
      val inFire = s_axis_a_tvalid && s_axis_b_tvalid
      core.io.a := s_axis_a_tdata
      core.io.b := s_axis_b_tdata
      s_axis_a_tready := true.B
      s_axis_b_tready := true.B
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(inFire, XilinxFpTargetConfig.MulLatency)
      m_axis_result_tdata := ShiftRegister(core.io.out, XilinxFpTargetConfig.MulLatency)
    }
  }
}

class XilinxFpCompareCompat(val compareKind: String) extends Module {
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val s_axis_b_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_b_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_b_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(8.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpBinaryIpNoResultReady(XilinxFpIpName.compare(compareKind), resultWidth = 8))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := s_axis_a_tdata
    ip.s_axis_b_tvalid := s_axis_b_tvalid
    ip.s_axis_b_tdata := s_axis_b_tdata
    s_axis_a_tready := ip.s_axis_a_tready
    s_axis_b_tready := ip.s_axis_b_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatCompareCore)
      val inFire = s_axis_a_tvalid && s_axis_b_tvalid
      val resultBit = Wire(Bool())
      core.io.a := s_axis_a_tdata
      core.io.b := s_axis_b_tdata
      resultBit := (compareKind match {
        case "lt" => core.io.lt
        case "eq" => core.io.eq
        case _ => core.io.gt
      })
      s_axis_a_tready := true.B
      s_axis_b_tready := true.B
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(inFire, XilinxFpTargetConfig.CompareLatency)
      m_axis_result_tdata := ShiftRegister(Cat(0.U(7.W), resultBit.asUInt), XilinxFpTargetConfig.CompareLatency)
    }
  }
}

class XilinxFpIntToFloatCompat(val intWidth: Int, val signedIn: Boolean) extends Module {
  private val axisInWidth = XilinxFpCompatUtil.axisByteWidth(intWidth)
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(intWidth.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(FP32_WIDTH.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpUnaryIpNoResultReady(XilinxFpIpName.intToFloat(intWidth, signedIn), axisInWidth, FP32_WIDTH))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := Cat(0.U((axisInWidth - intWidth).W), s_axis_a_tdata)
    s_axis_a_tready := ip.s_axis_a_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatIntToFpCore(intWidth, signedIn))
      core.io.in := s_axis_a_tdata
      s_axis_a_tready := true.B
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(s_axis_a_tvalid, XilinxFpTargetConfig.FixedToFloatLatency)
      m_axis_result_tdata := ShiftRegister(core.io.out, XilinxFpTargetConfig.FixedToFloatLatency)
    }
  }
}

class XilinxFpFloatToIntCompat(val intWidth: Int, val signedOut: Boolean) extends Module {
  private val axisOutWidth = XilinxFpCompatUtil.axisByteWidth(intWidth)
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(intWidth.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpUnaryIpNoResultReady(XilinxFpIpName.floatToInt(intWidth, signedOut), FP32_WIDTH, axisOutWidth))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := s_axis_a_tdata
    s_axis_a_tready := ip.s_axis_a_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata(intWidth - 1, 0)
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatFpToIntCore(intWidth, signedOut))
      core.io.in := s_axis_a_tdata
      s_axis_a_tready := true.B
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(s_axis_a_tvalid, XilinxFpTargetConfig.FloatToFixedLatency)
      m_axis_result_tdata := ShiftRegister(core.io.out, XilinxFpTargetConfig.FloatToFixedLatency)
    }
  }
}

class XilinxFpDivCompat extends Module {
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val s_axis_b_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_b_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_b_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(FP32_WIDTH.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpBinaryIpNoResultReady(XilinxFpIpName.div))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := s_axis_a_tdata
    ip.s_axis_b_tvalid := s_axis_b_tvalid
    ip.s_axis_b_tdata := s_axis_b_tdata
    s_axis_a_tready := ip.s_axis_a_tready
    s_axis_b_tready := ip.s_axis_b_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatDivSqrtCore(false))
      val pad = XilinxFpTargetConfig.DivSqrtPadLatency
      core.io.inValid := s_axis_a_tvalid && s_axis_b_tvalid
      core.io.a := s_axis_a_tdata
      core.io.b := s_axis_b_tdata
      s_axis_a_tready := core.io.inReady
      s_axis_b_tready := core.io.inReady
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(core.io.outValid, pad)
      m_axis_result_tdata := ShiftRegister(core.io.out, pad)
    }
  }
}

class XilinxFpSqrtCompat extends Module {
  val aclk = XilinxFpCompatUtil.keep(IO(Input(Clock())))
  val s_axis_a_tvalid = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val s_axis_a_tready = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val s_axis_a_tdata = XilinxFpCompatUtil.keep(IO(Input(UInt(FP32_WIDTH.W))))
  val m_axis_result_tvalid = XilinxFpCompatUtil.keep(IO(Output(Bool())))
  val m_axis_result_tready = XilinxFpCompatUtil.keep(IO(Input(Bool())))
  val m_axis_result_tdata = XilinxFpCompatUtil.keep(IO(Output(UInt(FP32_WIDTH.W))))

  if (FpBackend.useVivadoIp) {
    val ip = Module(new VivadoFpUnaryIpNoResultReady(XilinxFpIpName.sqrt, FP32_WIDTH, FP32_WIDTH))
    ip.aclk := aclk
    ip.s_axis_a_tvalid := s_axis_a_tvalid
    ip.s_axis_a_tdata := s_axis_a_tdata
    s_axis_a_tready := ip.s_axis_a_tready
    m_axis_result_tvalid := ip.m_axis_result_tvalid
    m_axis_result_tdata := ip.m_axis_result_tdata
  } else {
    withClockAndReset(aclk, reset) {
      val core = Module(new HardFloatDivSqrtCore(true))
      val pad = XilinxFpTargetConfig.DivSqrtPadLatency
      core.io.inValid := s_axis_a_tvalid
      core.io.a := s_axis_a_tdata
      core.io.b := 0.U
      s_axis_a_tready := core.io.inReady
      m_axis_result_tvalid := XilinxFpCompatUtil.delayValid(core.io.outValid, pad)
      m_axis_result_tdata := ShiftRegister(core.io.out, pad)
    }
  }
}

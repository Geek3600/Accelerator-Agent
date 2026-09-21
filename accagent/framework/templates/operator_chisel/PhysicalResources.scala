package spatialaccagent.templates

import chisel3._
import chisel3.experimental.{ExtModule, IntParam, StringParam}
import chisel3.util._

object PhysicalImplementation {
  private var activationMemoryBackend = "xpm_bram"
  private var fifoMemoryBackend = "xpm_bram"
  private var largeCacheMemoryBackend = "xpm_uram"
  private var fifoDepthOverride = 0
  private var weightBankCount = 1
  private var activationBankCount = 1
  private var weightBanksByRole = Map.empty[String, Int]

  def configureFpgaIp(
    computeBackend: String,
    weightMemory: String,
    activationMemory: String,
    fifoMemory: String,
    largeCacheMemory: String,
    fifoDepth: Int,
    weightBanks: Int,
    activationBanks: Int,
    roleWeightBanks: Map[String, Int]
  ): Unit = {
    require(computeBackend == "vivado_fp_ip", s"unsupported compute backend: $computeBackend")
    require(weightMemory == "xpm_uram", s"weights must use XPM URAM, got: $weightMemory")
    require(activationMemory == "xpm_bram", s"activations must use XPM BRAM, got: $activationMemory")
    require(fifoMemory == "xpm_bram", s"FIFOs must use XPM BRAM, got: $fifoMemory")
    require(largeCacheMemory == "xpm_uram", s"large caches must use XPM URAM, got: $largeCacheMemory")
    require(fifoDepth > 0, s"FIFO depth must be positive, got: $fifoDepth")
    require(weightBanks > 0, s"weight bank count must be positive, got: $weightBanks")
    require(activationBanks > 0, s"activation bank count must be positive, got: $activationBanks")
    require(roleWeightBanks.values.forall(_ > 0), s"role weight-bank counts must be positive: $roleWeightBanks")
    activationMemoryBackend = activationMemory
    fifoMemoryBackend = fifoMemory
    largeCacheMemoryBackend = largeCacheMemory
    fifoDepthOverride = fifoDepth
    weightBankCount = weightBanks
    activationBankCount = activationBanks
    weightBanksByRole = roleWeightBanks
  }

  // Compatibility entrypoints for already-materialized harnesses. Both
  // paths resolve to the same physical Vivado/XPM configuration; there is no
  // behavioral or HardFloat backend behind these adapters.
  def setSimulation(): Unit = configureFpgaIp(
    "vivado_fp_ip", "xpm_uram", "xpm_bram", "xpm_bram", "xpm_uram", 1, 1, 1, Map.empty
  )

  def setVivado(
    computeBackend: String,
    weightMemory: String,
    activationMemory: String,
    fifoMemory: String
  ): Unit = configureFpgaIp(
    computeBackend,
    weightMemory,
    activationMemory,
    fifoMemory,
    "xpm_uram",
    1,
    1,
    1,
    Map.empty
  )

  def resolveFifoDepth(requested: Int): Int = {
    require(requested > 0, s"requested FIFO depth must be positive, got: $requested")
    if (fifoDepthOverride > 0) requested max fifoDepthOverride else requested
  }

  def memoryBanks(role: String): Int = role match {
    case value if value == "weight" || value.startsWith("weight_") =>
      weightBanksByRole.getOrElse(value, weightBankCount)
    case "activation" => activationBankCount
    case _ => 1
  }

  def memoryPrimitive(role: String): String = role match {
    case value if value == "weight" || value.startsWith("weight_") =>
      "ultra"
    case "fifo" => if (fifoMemoryBackend == "xpm_bram") "block" else "ultra"
    // OPT's attention/KV-scale state uses XPM URAM explicitly.  Leaving
    // this as "auto" would permit an implementation-dependent mapping and
    // make the DSE resource model disagree with the final board build.
    case "cache" => if (largeCacheMemoryBackend == "xpm_uram") "ultra" else "block"
    case _ => if (activationMemoryBackend == "xpm_bram") "block" else "ultra"
  }
}

object PhysicalFpLatency {
  val Add = 12
  val Mul = 9
  val Div = 29
  val Sqrt = 29
  val Compare = 3
  val Convert = 7
}

private class VivadoFpBinary(moduleName: String, resultWidth: Int = 32) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(32.W)))
  val s_axis_b_tvalid = IO(Input(Bool()))
  val s_axis_b_tready = IO(Output(Bool()))
  val s_axis_b_tdata = IO(Input(UInt(32.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(resultWidth.W)))
}

private class VivadoFpUnary(moduleName: String, inputWidth: Int, resultWidth: Int) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(inputWidth.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(resultWidth.W)))
}

private class VivadoFpIntToFloat(moduleName: String, inputWidth: Int) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(inputWidth.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(32.W)))
}

private class VivadoFpFloatToInt(moduleName: String, outputWidth: Int) extends ExtModule {
  override def desiredName: String = moduleName
  val aclk = IO(Input(Clock()))
  val s_axis_a_tvalid = IO(Input(Bool()))
  val s_axis_a_tready = IO(Output(Bool()))
  val s_axis_a_tdata = IO(Input(UInt(32.W)))
  val m_axis_result_tvalid = IO(Output(Bool()))
  val m_axis_result_tdata = IO(Output(UInt(outputWidth.W)))
}

class PhysicalFp32Binary(moduleName: String, resultWidth: Int = 32) extends Module {
  val io = IO(new Bundle {
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val a = Input(UInt(32.W))
    val b = Input(UInt(32.W))
    val outValid = Output(Bool())
    val out = Output(UInt(resultWidth.W))
  })

  private val ip = Module(new VivadoFpBinary(moduleName, resultWidth))
  private val ready = ip.s_axis_a_tready && ip.s_axis_b_tready
  private val fire = io.inValid && ready
  ip.aclk := clock
  ip.s_axis_a_tvalid := fire
  ip.s_axis_a_tdata := io.a
  ip.s_axis_b_tvalid := fire
  ip.s_axis_b_tdata := io.b
  io.inReady := ready
  io.outValid := ip.m_axis_result_tvalid
  io.out := ip.m_axis_result_tdata
}

class PhysicalFp32Add extends PhysicalFp32Binary("fp_add_sp_12")
class PhysicalFp32Sub extends PhysicalFp32Binary("fp_sub_sp_12")
class PhysicalFp32Mul extends PhysicalFp32Binary("fp_mul_sp_9")
class PhysicalFp32Div extends PhysicalFp32Binary("fp_div_sp_29")
class PhysicalFp32CompareLt extends PhysicalFp32Binary("fp_cmp_lt_sp_3", 8)

class PhysicalFp32Sqrt extends Module {
  val io = IO(new Bundle {
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val in = Input(UInt(32.W))
    val outValid = Output(Bool())
    val out = Output(UInt(32.W))
  })

  private val ip = Module(new VivadoFpUnary("fp_sqrt_sp_29", 32, 32))
  ip.aclk := clock
  ip.s_axis_a_tvalid := io.inValid && ip.s_axis_a_tready
  ip.s_axis_a_tdata := io.in
  io.inReady := ip.s_axis_a_tready
  io.outValid := ip.m_axis_result_tvalid
  io.out := ip.m_axis_result_tdata
}

private class XpmSinglePortRom(depth: Int, width: Int, initFile: String) extends BlackBox(
  Map(
    "ADDR_WIDTH_A" -> IntParam(log2Ceil(depth max 2)),
    "AUTO_SLEEP_TIME" -> IntParam(0),
    "CASCADE_HEIGHT" -> IntParam(0),
    "ECC_MODE" -> StringParam("no_ecc"),
    "MEMORY_INIT_FILE" -> StringParam(initFile),
    "MEMORY_INIT_PARAM" -> StringParam("0"),
    "MEMORY_OPTIMIZATION" -> StringParam("true"),
    "MEMORY_PRIMITIVE" -> StringParam("block"),
    "MEMORY_SIZE" -> IntParam(depth * width),
    "MESSAGE_CONTROL" -> IntParam(0),
    "READ_DATA_WIDTH_A" -> IntParam(width),
    "READ_LATENCY_A" -> IntParam(1),
    "READ_RESET_VALUE_A" -> StringParam("0"),
    "RST_MODE_A" -> StringParam("SYNC"),
    "USE_MEM_INIT" -> IntParam(1),
    "WAKEUP_TIME" -> StringParam("disable_sleep")
  )
) {
  override def desiredName: String = "xpm_memory_sprom"
  private val addrBits = log2Ceil(depth max 2)
  val io = IO(new Bundle {
    val sleep = Input(Bool())
    val clka = Input(Clock())
    val ena = Input(Bool())
    val regcea = Input(Bool())
    val addra = Input(UInt(addrBits.W))
    val douta = Output(UInt(width.W))
    val sbiterra = Output(Bool())
    val dbiterra = Output(Bool())
  })
}

class PhysicalRom(depth: Int, width: Int, initFile: String) extends Module {
  private val addrBits = log2Ceil(depth max 2)
  val io = IO(new Bundle {
    val readEn = Input(Bool())
    val readAddr = Input(UInt(addrBits.W))
    val readData = Output(UInt(width.W))
  })
  private val rom = Module(new XpmSinglePortRom(depth, width, initFile))
  rom.io.sleep := false.B
  rom.io.clka := clock
  rom.io.ena := io.readEn
  rom.io.regcea := true.B
  rom.io.addra := io.readAddr
  io.readData := rom.io.douta
}

/** IEEE-754 format adapters. Arithmetic remains in Vivado IP; these adapters
  * only repack the 16-bit and 32-bit encodings at the stream boundary. */
class PhysicalFp16ToFp32 extends Module {
  val io = IO(new Bundle {
    val in = Input(UInt(16.W))
    val out = Output(UInt(32.W))
  })
  val sign = io.in(15)
  val exponent = io.in(14, 10)
  val fraction = io.in(9, 0)
  val normalExponent = Cat(0.U(3.W), exponent) + 112.U
  io.out := Mux(
    exponent === 0.U,
    Cat(sign, 0.U(8.W), 0.U(23.W)),
    Cat(sign, normalExponent(7, 0), fraction, 0.U(13.W))
  )
}

class PhysicalFp32ToFp16 extends Module {
  val io = IO(new Bundle {
    val in = Input(UInt(32.W))
    val out = Output(UInt(16.W))
  })
  val sign = io.in(31)
  val exponent = io.in(30, 23)
  val fraction = io.in(22, 13)
  val halfExponent = exponent - 112.U
  io.out := Mux(
    exponent <= 112.U,
    Cat(sign, 0.U(15.W)),
    Cat(sign, halfExponent(4, 0), fraction)
  )
}

class PhysicalFp32ToSigned(width: Int) extends Module {
  require(width > 0 && width <= 64, s"signed conversion width must be in 1..64, got $width")
  val io = IO(new Bundle {
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val in = Input(UInt(32.W))
    val outValid = Output(Bool())
    val out = Output(SInt(width.W))
  })
  private val ip = Module(new VivadoFpFloatToInt(s"fp_f2i_s${width}_sp_7", width))
  ip.aclk := clock
  ip.s_axis_a_tvalid := io.inValid && ip.s_axis_a_tready
  ip.s_axis_a_tdata := io.in
  io.inReady := ip.s_axis_a_tready
  io.outValid := ip.m_axis_result_tvalid
  io.out := ip.m_axis_result_tdata.asSInt
}

class PhysicalUIntToFp32(width: Int) extends Module {
  require(width > 0 && width <= 64, s"unsigned conversion width must be in 1..64, got $width")
  val io = IO(new Bundle {
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val in = Input(UInt(width.W))
    val outValid = Output(Bool())
    val out = Output(UInt(32.W))
  })
  private val ip = Module(new VivadoFpIntToFloat(s"fp_i2f_u${width}_sp_7", width))
  ip.aclk := clock
  ip.s_axis_a_tvalid := io.inValid && ip.s_axis_a_tready
  ip.s_axis_a_tdata := io.in
  io.inReady := ip.s_axis_a_tready
  io.outValid := ip.m_axis_result_tvalid
  io.out := ip.m_axis_result_tdata
}

class PhysicalSignedToFp32(width: Int) extends Module {
  require(width > 0 && width <= 64, s"signed conversion width must be in 1..64, got $width")
  val io = IO(new Bundle {
    val inValid = Input(Bool())
    val inReady = Output(Bool())
    val in = Input(SInt(width.W))
    val outValid = Output(Bool())
    val out = Output(UInt(32.W))
  })
  private val ip = Module(new VivadoFpIntToFloat(s"fp_i2f_s${width}_sp_7", width))
  ip.aclk := clock
  ip.s_axis_a_tvalid := io.inValid && ip.s_axis_a_tready
  ip.s_axis_a_tdata := io.in.asUInt
  io.inReady := ip.s_axis_a_tready
  io.outValid := ip.m_axis_result_tvalid
  io.out := ip.m_axis_result_tdata
}

private class XpmSimpleDualPort(depth: Int, width: Int, primitive: String) extends BlackBox(
  Map(
    "ADDR_WIDTH_A" -> IntParam(log2Ceil(depth max 2)),
    "ADDR_WIDTH_B" -> IntParam(log2Ceil(depth max 2)),
    "AUTO_SLEEP_TIME" -> IntParam(0),
    "BYTE_WRITE_WIDTH_A" -> IntParam(width),
    "CASCADE_HEIGHT" -> IntParam(0),
    "CLOCKING_MODE" -> StringParam("common_clock"),
    "ECC_MODE" -> StringParam("no_ecc"),
    "MEMORY_INIT_FILE" -> StringParam("none"),
    "MEMORY_INIT_PARAM" -> StringParam("0"),
    "MEMORY_OPTIMIZATION" -> StringParam("true"),
    "MEMORY_PRIMITIVE" -> StringParam(primitive),
    "MEMORY_SIZE" -> IntParam(depth * width),
    "MESSAGE_CONTROL" -> IntParam(0),
    "READ_DATA_WIDTH_B" -> IntParam(width),
    "READ_LATENCY_B" -> IntParam(1),
    "READ_RESET_VALUE_B" -> StringParam("0"),
    "RST_MODE_A" -> StringParam("SYNC"),
    "RST_MODE_B" -> StringParam("SYNC"),
    "USE_EMBEDDED_CONSTRAINT" -> IntParam(0),
    "USE_MEM_INIT" -> IntParam(0),
    "WAKEUP_TIME" -> StringParam("disable_sleep"),
    "WRITE_DATA_WIDTH_A" -> IntParam(width),
    "WRITE_MODE_B" -> StringParam("read_first")
  )
) {
  override def desiredName: String = "xpm_memory_sdpram"
  private val addrBits = log2Ceil(depth max 2)
  val io = IO(new Bundle {
    val sleep = Input(Bool())
    val clka = Input(Clock())
    val ena = Input(Bool())
    val wea = Input(Bool())
    val addra = Input(UInt(addrBits.W))
    val dina = Input(UInt(width.W))
    val injectsbiterra = Input(Bool())
    val injectdbiterra = Input(Bool())
    val clkb = Input(Clock())
    val rstb = Input(Bool())
    val enb = Input(Bool())
    val regceb = Input(Bool())
    val addrb = Input(UInt(addrBits.W))
    val doutb = Output(UInt(width.W))
    val sbiterrb = Output(Bool())
    val dbiterrb = Output(Bool())
  })
}

class PhysicalSimpleDualPortMemory(depth: Int, width: Int, role: String) extends Module {
  private val addrBits = log2Ceil(depth max 2)
  private val banks = PhysicalImplementation.memoryBanks(role)
  // XPM does not accept a one-word bank. Keep the logical depth unchanged
  // while giving each physical bank the smallest legal addressable depth.
  private val bankDepth = math.max(2, (depth + banks - 1) / banks)
  private val bankAddrBits = log2Ceil(bankDepth max 2)
  val io = IO(new Bundle {
    val writeEn = Input(Bool())
    val writeAddr = Input(UInt(addrBits.W))
    val writeData = Input(UInt(width.W))
    val readEn = Input(Bool())
    val readAddr = Input(UInt(addrBits.W))
    val readData = Output(UInt(width.W))
  })

  private val memories = Seq.tabulate(banks) { index =>
    Module(new XpmSimpleDualPort(bankDepth, width, PhysicalImplementation.memoryPrimitive(role)))
  }
  private val bankBits = log2Ceil(banks max 2)
  // `% banks.U` may infer a narrower result than the logical bank selector
  // for mixed BRAM/URAM role layouts. Assign through the declared selector
  // width so every legal bank count, including one-bank roles, elaborates.
  private val writeBank = Wire(UInt(bankBits.W))
  private val readBank = Wire(UInt(bankBits.W))
  writeBank := io.writeAddr % banks.U
  readBank := io.readAddr % banks.U
  private val writeRow = (io.writeAddr / banks.U)(bankAddrBits - 1, 0)
  private val readRow = (io.readAddr / banks.U)(bankAddrBits - 1, 0)
  private val readBankReg = RegEnable(readBank, 0.U(bankBits.W), io.readEn)

  for ((mem, index) <- memories.zipWithIndex) {
    mem.io.sleep := false.B
    mem.io.clka := clock
    mem.io.ena := io.writeEn && writeBank === index.U
    mem.io.wea := io.writeEn && writeBank === index.U
    mem.io.addra := writeRow
    mem.io.dina := io.writeData
    mem.io.injectsbiterra := false.B
    mem.io.injectdbiterra := false.B
    mem.io.clkb := clock
    mem.io.rstb := reset.asBool
    mem.io.enb := io.readEn && readBank === index.U
    mem.io.regceb := true.B
    mem.io.addrb := readRow
  }
  io.readData := Mux1H(memories.zipWithIndex.map { case (mem, index) =>
    (readBankReg === index.U) -> mem.io.doutb
  })
}

/**
  * A small ready/valid FIFO backed by the same XPM RAM abstraction as the
  * rest of the generated accelerator.  Its registered read path matches the
  * one-cycle XPM read latency used in VCS and Vivado; no Chisel Queue or
  * inferred simulation-only memory is involved.
  */
class PhysicalStreamFifo[T <: Data](gen: T, requestedDepth: Int) extends Module {
  private val depth = PhysicalImplementation.resolveFifoDepth(requestedDepth)
  private val addrBits = log2Ceil(depth max 2)
  private val width = gen.getWidth

  val io = IO(new Bundle {
    val enq = Flipped(Decoupled(gen))
    val deq = Decoupled(gen)
  })

  private val memory = Module(new PhysicalSimpleDualPortMemory(depth, width, "fifo"))
  private val writePtr = RegInit(0.U(addrBits.W))
  private val readPtr = RegInit(0.U(addrBits.W))
  private val count = RegInit(0.U(log2Ceil(depth + 1).W))
  private val readPending = RegInit(false.B)
  private val outValid = RegInit(false.B)
  private val outBitsRaw = Reg(UInt(width.W))

  io.enq.ready := count =/= depth.U
  io.deq.valid := outValid
  io.deq.bits := outBitsRaw.asTypeOf(io.deq.bits)

  val enqFire = io.enq.fire
  val deqFire = io.deq.fire
  val issueRead = !outValid && !readPending && count =/= 0.U

  memory.io.writeEn := enqFire
  memory.io.writeAddr := writePtr
  memory.io.writeData := io.enq.bits.asUInt
  memory.io.readEn := issueRead
  memory.io.readAddr := readPtr

  when(enqFire) {
    writePtr := Mux(writePtr === (depth - 1).U, 0.U, writePtr + 1.U)
  }
  when(issueRead) {
    readPending := true.B
  }
  when(readPending) {
    outBitsRaw := memory.io.readData
    outValid := true.B
    readPending := false.B
  }
  when(deqFire) {
    outValid := false.B
    readPtr := Mux(readPtr === (depth - 1).U, 0.U, readPtr + 1.U)
  }

  switch(Cat(enqFire, deqFire)) {
    is("b10".U) { count := count + 1.U }
    is("b01".U) { count := count - 1.U }
  }
}

package QuantCommon

import chisel3._
import chisel3.experimental.{IntParam, StringParam}
import chisel3.util.log2Ceil

private class XpmUramSimpleDualPort(val depth: Int, val width: Int) extends BlackBox(
  Map(
    "ADDR_WIDTH_A" -> IntParam(log2Ceil(depth)),
    "ADDR_WIDTH_B" -> IntParam(log2Ceil(depth)),
    "AUTO_SLEEP_TIME" -> IntParam(0),
    "BYTE_WRITE_WIDTH_A" -> IntParam(width),
    "CASCADE_HEIGHT" -> IntParam(0),
    "CLOCKING_MODE" -> StringParam("common_clock"),
    "ECC_MODE" -> StringParam("no_ecc"),
    "MEMORY_INIT_FILE" -> StringParam("none"),
    "MEMORY_INIT_PARAM" -> StringParam("0"),
    "MEMORY_OPTIMIZATION" -> StringParam("true"),
    "MEMORY_PRIMITIVE" -> StringParam("ultra"),
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

  private val addrWidth = log2Ceil(depth)
  val io = IO(new Bundle {
    val sleep = Input(Bool())
    val clka = Input(Clock())
    val ena = Input(Bool())
    val wea = Input(Bool())
    val addra = Input(UInt(addrWidth.W))
    val dina = Input(UInt(width.W))
    val injectsbiterra = Input(Bool())
    val injectdbiterra = Input(Bool())
    val clkb = Input(Clock())
    val rstb = Input(Bool())
    val enb = Input(Bool())
    val regceb = Input(Bool())
    val addrb = Input(UInt(addrWidth.W))
    val doutb = Output(UInt(width.W))
    val sbiterrb = Output(Bool())
    val dbiterrb = Output(Bool())
  })
}

class XilinxUramCompatMem(val depth: Int, val width: Int) extends Module {
  private val addrWidth = log2Ceil(depth)

  val io = IO(new Bundle {
    val write_en = Input(Bool())
    val write_addr = Input(UInt(addrWidth.W))
    val write_data = Input(UInt(width.W))
    val read_en = Input(Bool())
    val read_addr = Input(UInt(addrWidth.W))
    val read_data = Output(UInt(width.W))
  })

  val readValid = RegNext(io.read_en, false.B)

  if (FpBackend.useVivadoIp && width == 72 && depth > 4096 && depth <= 8192) {
    val segDepth = 4096
    val segAddrWidth = log2Ceil(segDepth)
    val lowMem = Module(new XpmUramSimpleDualPort(segDepth, width))
    val highMem = Module(new XpmUramSimpleDualPort(segDepth, width))
    val writeHigh = io.write_addr >= segDepth.U(addrWidth.W)
    val readHigh = io.read_addr >= segDepth.U(addrWidth.W)
    val readHighR = RegNext(readHigh, false.B)
    val writeAddr = io.write_addr(segAddrWidth - 1, 0)
    val readAddr = io.read_addr(segAddrWidth - 1, 0)

    lowMem.io.sleep := false.B
    lowMem.io.clka := clock
    lowMem.io.ena := io.write_en && !writeHigh
    lowMem.io.wea := io.write_en && !writeHigh
    lowMem.io.addra := writeAddr
    lowMem.io.dina := io.write_data
    lowMem.io.injectsbiterra := false.B
    lowMem.io.injectdbiterra := false.B
    lowMem.io.clkb := clock
    lowMem.io.rstb := false.B
    lowMem.io.enb := io.read_en && !readHigh
    lowMem.io.regceb := true.B
    lowMem.io.addrb := readAddr

    highMem.io.sleep := false.B
    highMem.io.clka := clock
    highMem.io.ena := io.write_en && writeHigh
    highMem.io.wea := io.write_en && writeHigh
    highMem.io.addra := writeAddr
    highMem.io.dina := io.write_data
    highMem.io.injectsbiterra := false.B
    highMem.io.injectdbiterra := false.B
    highMem.io.clkb := clock
    highMem.io.rstb := false.B
    highMem.io.enb := io.read_en && readHigh
    highMem.io.regceb := true.B
    highMem.io.addrb := readAddr

    io.read_data := Mux(readValid, Mux(readHighR, highMem.io.doutb, lowMem.io.doutb), 0.U)
  } else if (FpBackend.useVivadoIp) {
    val mem = Module(new XpmUramSimpleDualPort(depth, width))
    mem.io.sleep := false.B
    mem.io.clka := clock
    mem.io.ena := io.write_en
    mem.io.wea := io.write_en
    mem.io.addra := io.write_addr
    mem.io.dina := io.write_data
    mem.io.injectsbiterra := false.B
    mem.io.injectdbiterra := false.B
    mem.io.clkb := clock
    mem.io.rstb := false.B
    mem.io.enb := io.read_en
    mem.io.regceb := true.B
    mem.io.addrb := io.read_addr
    io.read_data := Mux(readValid, mem.io.doutb, 0.U)
  } else {
    val mem = SyncReadMem(depth, UInt(width.W))
    when(io.write_en) {
      mem.write(io.write_addr, io.write_data)
    }
    val rawRead = mem.read(io.read_addr, io.read_en)
    io.read_data := Mux(readValid, rawRead, 0.U)
  }
}

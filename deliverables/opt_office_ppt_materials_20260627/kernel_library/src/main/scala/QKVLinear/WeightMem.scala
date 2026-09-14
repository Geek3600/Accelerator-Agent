package QKVLinear

import QuantCommon.XilinxUramCompatMem
import chisel3._
import chisel3.util._
import QKVLinear.Param._

// WeightMem: 片上权重存储模块
// 当前扩展为 active/shadow 双 bank：
// - active bank 供计算读取
// - shadow bank 供 wrapper 后台 preload 写入
// 旧的 init_mode 路径仍保留，默认写 bank0，用于单层兼容模式
class WeightMem extends Module {
  val io = IO(new Bundle {
    val init_mode = Input(Bool())
    val init_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val init_data = Input(UInt(WMEM_WIDTH.W))
    val init_wen = Input(Bool())

    val preload_valid = Input(Bool())
    val preload_bank = Input(Bool())
    val preload_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val preload_data = Input(UInt(WMEM_WIDTH.W))

    val read_en = Input(Bool())
    val read_bank = Input(Bool())
    val read_addr = Input(UInt(log2Up(ROWBLOCK * COLBLOCK).W))
    val read_data = Output(Vec(ROW, UInt(WMEM_WIDTH.W)))
  })

  val TILE_DEPTH = ROWBLOCK * COLBLOCK
  val BANK_DEPTH = TILE_DEPTH
  val NUM_SLICES = 4
  val SLICE_WIDTH = 72

  val weight_banks = Seq.fill(2)(
    Seq.fill(ROW)(
      Seq.fill(NUM_SLICES)(Module(new XilinxUramCompatMem(BANK_DEPTH, SLICE_WIDTH)))
    )
  )

  val legacyWrite = io.init_mode && io.init_wen
  val preloadValidR = RegNext(io.preload_valid, false.B)
  // These staged payload regs are only sampled under preloadValid/writeFire, so
  // they do not need reset. Leaving them unreset avoids dragging long reset
  // trees onto large data buses and write controls.
  val preloadBankR = Reg(Bool())
  val preloadAddrR = Reg(UInt(log2Up(WMEM_DEPTH).W))
  val preloadDataR = Reg(UInt(WMEM_WIDTH.W))
  val preloadColBlockR = RegInit(0.U(log2Up(COLBLOCK).W))
  val preloadRowSelR = RegInit(0.U(log2Up(ROW).W))
  val preloadRowBlockR = RegInit(0.U(log2Up(ROWBLOCK).W))
  val preloadTileAddrR = RegInit(0.U(log2Up(TILE_DEPTH).W))
  when(io.preload_valid) {
    preloadBankR := io.preload_bank
    preloadAddrR := io.preload_addr
    preloadDataR := io.preload_data
    when(io.preload_addr === 0.U) {
      preloadColBlockR := 0.U
      preloadRowSelR := 0.U
      preloadRowBlockR := 0.U
      preloadTileAddrR := 0.U
    }.elsewhen(preloadColBlockR === (COLBLOCK - 1).U) {
      preloadColBlockR := 0.U
      when(preloadRowSelR === (ROW - 1).U) {
        preloadRowSelR := 0.U
        preloadRowBlockR := preloadRowBlockR + 1.U
        preloadTileAddrR := preloadRowBlockR + 1.U
      }.otherwise {
        preloadRowSelR := preloadRowSelR + 1.U
        preloadTileAddrR := preloadRowBlockR
      }
    }.otherwise {
      preloadColBlockR := preloadColBlockR + 1.U
      preloadTileAddrR := preloadTileAddrR + ROWBLOCK.U
    }
  }
  val preloadWrite = preloadValidR
  assert(!(legacyWrite && preloadWrite), "QKV WeightMem legacy init and preload collided")

  val writeBank = Mux(preloadWrite, preloadBankR, false.B)
  val writeAddr = Mux(preloadWrite, preloadAddrR, io.init_addr)
  val writeData = Mux(preloadWrite, preloadDataR, io.init_data)
  val writeFire = legacyWrite || preloadWrite
  val legacyWriteColBlock = io.init_addr % COLBLOCK.U
  val legacyWriteRowLinear = io.init_addr / COLBLOCK.U
  val legacyWriteRowSel = legacyWriteRowLinear % ROW.U
  val legacyWriteRowBlock = legacyWriteRowLinear / ROW.U
  val legacyWriteTileAddr = legacyWriteColBlock * ROWBLOCK.U + legacyWriteRowBlock
  val writeRowSel = Mux(preloadWrite, preloadRowSelR, legacyWriteRowSel)
  val writeTileAddr = Mux(preloadWrite, preloadTileAddrR, legacyWriteTileAddr)
  val memWriteBankR = Reg(Bool())
  val memWriteTileAddrR = Reg(UInt(log2Up(TILE_DEPTH).W))
  val memWriteDataR = Reg(UInt(WMEM_WIDTH.W))
  val memWriteRowEnR = Reg(Vec(ROW, Bool()))
  when(writeFire) {
    memWriteBankR := writeBank
    memWriteTileAddrR := writeTileAddr
    memWriteDataR := writeData
  }
  for (b <- 0 until ROW) {
    memWriteRowEnR(b) := writeFire && writeRowSel === b.U
  }

  for (copy <- 0 until 2) {
    for (b <- 0 until ROW) {
      for (s <- 0 until NUM_SLICES) {
        weight_banks(copy)(b)(s).io.write_en := memWriteRowEnR(b) && memWriteBankR === (copy == 1).B
        weight_banks(copy)(b)(s).io.write_addr := memWriteTileAddrR
        weight_banks(copy)(b)(s).io.write_data := memWriteDataR((s + 1) * SLICE_WIDTH - 1, s * SLICE_WIDTH)
        weight_banks(copy)(b)(s).io.read_en := io.read_en
        weight_banks(copy)(b)(s).io.read_addr := io.read_addr
      }
    }
  }

  val readDatas = for (copy <- 0 until 2) yield {
    for (b <- 0 until ROW) yield {
      val slices = for (s <- 0 until NUM_SLICES) yield {
        weight_banks(copy)(b)(s).io.read_data
      }
      Cat(slices.reverse)
    }
  }

  val selectedCopy = RegNext(io.read_bank, false.B)
  for (i <- 0 until ROW) {
    io.read_data(i) := Mux(selectedCopy, readDatas(1)(i), readDatas(0)(i))
  }
}

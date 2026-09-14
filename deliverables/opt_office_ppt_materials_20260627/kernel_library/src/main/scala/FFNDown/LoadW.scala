package FFNDown

import FFNDown.Param._
import chisel3._
import chisel3.util._

class LoadWeight extends Module {
  val io = IO(new Bundle() {
    val update = Input(Bool())
    val st = Input(Bool())

    val init_mode = Input(Bool())
    val init_data = Input(UInt(WMEM_WIDTH.W))
    val init_addr = Output(UInt(log2Up(WMEM_DEPTH).W))

    val active_bank = Input(Bool())
    val preload_valid = Input(Bool())
    val preload_bank = Input(Bool())
    val preload_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val preload_data = Input(UInt(WMEM_WIDTH.W))

    val data_out = Output(Vec(ROW, UInt(WMEM_WIDTH.W)))
    val data_out_valid = Output(Bool())
    val data_out_sel = Output(Bool())
    val weight_ready = Output(Bool())
  })

  val weight_mem = Module(new WeightMem)
  val TILE_DEPTH = ROWBLOCK * COLBLOCK
  val nextTileIdx = RegInit(0.U(log2Up(TILE_DEPTH).W))
  val nextWriteSel = RegInit(false.B)
  val firstTilePending = RegInit(false.B)
  val legacyInitAddr = RegInit(0.U(log2Up(WMEM_DEPTH).W))
  val startupIssue = io.st && !io.init_mode
  val issueRead = (io.st || io.update) && !io.init_mode
  val issueTileIdx = Mux(io.st, 0.U, nextTileIdx)
  val issueWriteSel = Mux(io.st, false.B, nextWriteSel)
  val issueLastTile = issueTileIdx === (TILE_DEPTH - 1).U

  when(io.init_mode) {
    legacyInitAddr := Mux(legacyInitAddr === (WMEM_DEPTH - 1).U, 0.U, legacyInitAddr + 1.U)
  }

  weight_mem.io.init_mode := io.init_mode
  weight_mem.io.init_addr := legacyInitAddr
  weight_mem.io.init_data := io.init_data
  weight_mem.io.init_wen := io.init_mode
  weight_mem.io.preload_valid := io.preload_valid
  weight_mem.io.preload_bank := io.preload_bank
  weight_mem.io.preload_addr := io.preload_addr
  weight_mem.io.preload_data := io.preload_data
  weight_mem.io.read_en := issueRead
  weight_mem.io.read_bank := io.active_bank
  weight_mem.io.read_addr := issueTileIdx

  when(io.st) {
    nextTileIdx := 1.U
    nextWriteSel := true.B
    firstTilePending := true.B
  }.elsewhen(issueRead) {
    nextTileIdx := Mux(issueLastTile, 0.U, issueTileIdx + 1.U)
    nextWriteSel := ~issueWriteSel
  }

  when(RegNext(startupIssue, false.B)) {
    firstTilePending := false.B
  }

  io.init_addr := legacyInitAddr
  io.data_out := weight_mem.io.read_data
  io.data_out_valid := RegNext(issueRead, false.B)
  io.data_out_sel := RegNext(issueWriteSel, false.B)
  io.weight_ready := !firstTilePending
}

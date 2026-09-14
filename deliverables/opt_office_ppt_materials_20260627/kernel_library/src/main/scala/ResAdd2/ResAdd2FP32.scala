package ResAdd2

import QuantCommon.Fp32VecAdd
import QuantCommon.XilinxFpTargetConfig
import ResAdd2.FP32Param._
import chisel3._
import chisel3.util._

// ResAdd2FP32: FFN 后浮点残差连接
class ResAdd2FP32 extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    val s7_in = Input(UInt(DATA_WIDTH.W))
    val s7_in_st = Input(Bool())
    val s7_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val s7_in_valid = Input(Bool())
    val s7_in_last = Input(Bool())
    val s7_ready = Output(Bool())

    val ffn_in = Input(UInt(DATA_WIDTH.W))
    val ffn_in_st = Input(Bool())
    val ffn_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val ffn_in_valid = Input(Bool())
    val ffn_in_last = Input(Bool())
    val ffn_ready = Output(Bool())

    val res = Output(UInt(DATA_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  val mem = Module(new DataMem(MEM_DEPTH, DATA_WIDTH, 3))

  mem.io.w_st := io.s7_in_st
  mem.io.w_last := io.s7_in_last
  mem.io.w_data := io.s7_in
  mem.io.w_addr := io.s7_in_addr
  mem.io.w_valid := io.s7_in_valid

  io.s7_ready := mem.io.w_ready

  val idle :: reading :: Nil = Enum(2)
  val state = RegInit(idle)

  val is_idle = state === idle
  val is_reading = state === reading

  val fire = io.ffn_in_valid && io.res_ready
  // Never advance into the adder unless an S7 residual buffer is actually readable.
  val active = mem.io.r_ready && fire

  switch(state) {
    is(idle) {
      when(mem.io.r_ready && io.ffn_in_valid) {
        state := reading
      }
    }
    is(reading) {
      when(io.ffn_in_last && fire) {
        when(mem.io.r_ready && io.ffn_in_valid) {
          state := reading
        }.otherwise {
          state := idle
        }
      }
    }
  }

  mem.io.r_addr := io.ffn_in_addr
  mem.io.r_en := active
  mem.io.r_last := active && io.ffn_in_last

  val ffn_data_r = Reg(UInt(DATA_WIDTH.W))
  when(active) {
    ffn_data_r := io.ffn_in
  }
  val ffn_valid_r = RegNext(active, false.B)
  val ffn_st_r = Reg(Bool())
  val ffn_last_r = Reg(Bool())
  val ffn_addr_r = Reg(UInt(log2Up(MEM_DEPTH).W))
  when(active) {
    ffn_st_r := io.ffn_in_st
    ffn_last_r := io.ffn_in_last
    ffn_addr_r := io.ffn_in_addr
  }

  val add = Module(new Fp32VecAdd)
  add.io.a := Mux(ffn_valid_r, mem.io.r_data, 0.U(DATA_WIDTH.W))
  add.io.b := Mux(ffn_valid_r, ffn_data_r, 0.U(DATA_WIDTH.W))

  val resValidPipe = RegInit(VecInit(Seq.fill(XilinxFpTargetConfig.AddLatency)(false.B)))
  val resStPipe = Reg(Vec(XilinxFpTargetConfig.AddLatency, Bool()))
  val resLastPipe = Reg(Vec(XilinxFpTargetConfig.AddLatency, Bool()))
  val resAddrPipe = Reg(Vec(XilinxFpTargetConfig.AddLatency, UInt(log2Up(MEM_DEPTH).W)))

  resValidPipe(0) := ffn_valid_r
  resStPipe(0) := ffn_st_r
  resLastPipe(0) := ffn_last_r
  resAddrPipe(0) := ffn_addr_r
  for (i <- 1 until XilinxFpTargetConfig.AddLatency) {
    resValidPipe(i) := resValidPipe(i - 1)
    resStPipe(i) := resStPipe(i - 1)
    resLastPipe(i) := resLastPipe(i - 1)
    resAddrPipe(i) := resAddrPipe(i - 1)
  }

  io.res := add.io.out
  io.res_valid := resValidPipe.last
  io.res_st := resStPipe.last
  io.res_last := resLastPipe.last
  io.res_addr := resAddrPipe.last

  io.ffn_ready := mem.io.r_ready && io.res_ready
}

object ResAdd2FP32Gen extends App {
  emitVerilog(new ResAdd2FP32, Array("--target-dir", "generated"))
}

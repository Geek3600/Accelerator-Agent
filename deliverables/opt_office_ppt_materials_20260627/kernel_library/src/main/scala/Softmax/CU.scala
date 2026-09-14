package Softmax

import chisel3._
import chisel3.util._
import Param._

class CU extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt((MEM_WIDTH).W))
    val data_in_valid = Input(Bool())

    val data_in_w = Input(UInt((WMEM_WIDTH).W))
    val data_in_w_valid = Input(Bool())

    val data_out = Output(UInt((MEM_WIDTH).W))
    val data_out_valid = Output(Bool())
  })
    val softmax = Module(new Softmax)

    val in_vec = io.data_in.asTypeOf(Vec(V, SInt(DATAW.W)))
    softmax.io.in := Mux(io.data_in_valid, in_vec, VecInit(Seq.fill(V)(0.S(DATAW.W))))

    val in_mask = io.data_in_w.asTypeOf(Vec(V, Bool()))
    softmax.io.in_mask := Mux(io.data_in_w_valid, in_mask, VecInit(Seq.fill(V)(false.B))) 

    val out_vec = Wire(Vec(V, UInt(DATAW.W)))
    out_vec := softmax.io.out.map(_.asUInt)

    io.data_out := Cat(out_vec.reverse)   
    io.data_out_valid := io.data_in_valid
    // printf(p"[CU] data_in_valid = ${io.data_in_valid}, data_out_valid = ${io.data_out_valid}, data_in: ${Binary(io.data_in)}, data_out: ${Binary(io.data_out)}\n")
}

object CU extends App {
  emitVerilog(new CU, Array("--target-dir", "generated"))
}

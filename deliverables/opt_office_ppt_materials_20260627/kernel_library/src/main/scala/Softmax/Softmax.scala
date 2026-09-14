package Softmax

import Param._
import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

class Softmax extends Module {
  val io = IO(new Bundle {
    val in  = Input(Vec(V, SInt(DATAW.W)))  
    val in_mask = Input(Vec(V, Bool()))
    val out = Output(Vec(V, SInt((DATAW).W))) 
  })
     
    val FRAC_WIDTH = 8 // 小数部分位宽
    val INT_WIDTH = DATAW // 整数部分位宽
    val FIXED_WIDTH = INT_WIDTH + FRAC_WIDTH // 定点数位宽 

    // 常量
    val log2e = "b0000000101110001".U(FIXED_WIDTH.W) // 1.4427 

    val log2 = Module(new Log2(1, INT_WIDTH, FRAC_WIDTH))
    val exp2_1 = Module(new Exp2(V, INT_WIDTH, FRAC_WIDTH))
    val exp2_2 = Module(new Exp2(V, INT_WIDTH, FRAC_WIDTH))
    val maxPreProcess = Module(new MaxPreProcess(V, INT_WIDTH, FRAC_WIDTH))
    val sum = Module(new Sum(V, INT_WIDTH, FRAC_WIDTH))

    val fixInput = Wire(Vec(V, SInt(FIXED_WIDTH.W)))
    val xs = Wire(Vec(V, SInt(FIXED_WIDTH.W)))
    val xs_mul_log2e_fixwidth = Wire(Vec(V, SInt((FIXED_WIDTH).W)))
    val xs_mul_log2e_fullwidth = Wire(Vec(V, SInt((2*FIXED_WIDTH).W)))

    val negInf = Wire(SInt(DATAW.W))
    negInf := (1.U << (DATAW - 1)).asSInt

    val maskedInput = Wire(Vec(V, SInt(DATAW.W)))
    io.in.zip(io.in_mask).zipWithIndex.foreach { case ((data, mask), i) =>
        maskedInput(i) := Mux(mask, data, negInf)
    }

    // 找最大值，并做减法
    maxPreProcess.io.in := maskedInput
    xs := maxPreProcess.io.out

    // 先转成定点数
    for (i <- 0 until V) {
        fixInput(i) := Cat(xs(i).asUInt, 0.U(FRAC_WIDTH.W)).asSInt
    }
    

    // 乘log2e
    for (i <- 0 until V) {
        xs_mul_log2e_fullwidth(i) :=  xs(i) * log2e
        xs_mul_log2e_fixwidth(i) := xs_mul_log2e_fullwidth(i)(FRAC_WIDTH+FIXED_WIDTH-1, FRAC_WIDTH).asSInt    
    }

    // 指数运算
    exp2_1.io.in := xs_mul_log2e_fixwidth
    val exs = Wire(Vec(V, SInt(FIXED_WIDTH.W)))
    exs := exp2_1.io.out

    // 求和
    sum.io.in := exs
    val sum_res = Wire(SInt(FIXED_WIDTH.W))
    sum_res := sum.io.out

    // 求对数
    log2.io.in := sum_res.asTypeOf(Vec(1, SInt(FIXED_WIDTH.W)))
    val lxs = Wire(SInt(FIXED_WIDTH.W))
    lxs := log2.io.out(0)

    // 先乘log2e，再减去lxs
    val xs_hat = Wire(Vec(V, SInt(FIXED_WIDTH.W)))
    for (i <- 0 until V) {
        xs_hat(i) := xs_mul_log2e_fixwidth(i) - lxs
    }

    // 指数运算
    exp2_2.io.in := xs_hat
    val res = Wire(Vec(V, SInt(FIXED_WIDTH.W)))
    res := exp2_2.io.out

    // 反量化
    val maxInt8 = 127.S
    val minInt8 = (-128).S
    for (i <- 0 until V) {
        val y_round = res(i) + (1 << (FRAC_WIDTH - 1)).S // +0.5
        val y_int_tmp = y_round >> FRAC_WIDTH   // 舍入
        val y_int8 = Mux( // 饱和截断
             y_int_tmp > maxInt8, maxInt8,
             Mux(y_int_tmp < minInt8, minInt8, y_int_tmp)
        )
        io.out(i) := y_int8.asSInt
    }

}

object Softmax extends App {
    ChiselStage.emitSystemVerilogFile(
        new Softmax,
        firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
    )
}
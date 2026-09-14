// package Softmax

// import Param._
// import chisel3._
// import chisel3.util._

// //这里相对于标准的mem，增加了一个状态机，描述片上存储的状态是正在写，写完了，还是空的 三者分别是buzy，full，以及empey
// //手动算一下，可能的组合一共6种full full，full buzy，full empey，buzy buzy， buzy empey， empey empey
// //状态切换由w_st，w_last，r_last控制，分别表示开始写，写完，以及读完一个存储
// class DataMem(val depth: Int, val width: Int)extends Module{
//   val io = IO(new Bundle() {
//     val w_st = Input(Bool())
//     val w_last = Input(Bool())
//     val w_data = Input(UInt(MEM_WIDTH.W))
//     val w_addr = Input(UInt(log2Up(depth).W))
//     val w_valid = Input(Bool())
//     val w_ready = Output(Bool())


//     val r_last = Input(Bool())
//     val r_data = Output(UInt(MEM_WIDTH.W))
//     val r_addr = Input(UInt(log2Up(depth).W))
//     val r_ready = Output(Bool())
//   })
//   // be：写 busy + 读 empty（正在写第一个 buffer）
//   // bb: 写 busy + 读 busy（边写边读的重叠阶段
//   // fb: 写 full + 读 busy（写端满了，读端还在读）
//   val ee :: be :: bb ::  fb :: fe ::ff ::Nil = Enum(6)
//   val state= RegInit(ee)
//   val ff_mux = Mux(io.r_last,fe, ff)
//   val fb_mux = MuxLookup(
//     Cat(io.w_st, io.w_last, io.r_last),
//     fb
//   )(
//     List(
//       0.U -> fb,
//       1.U -> be,
//       2.U -> ff,
//       3.U -> fe
//     )
//   )
//   val fe_mux = MuxLookup(
//     Cat(io.w_st, io.w_last, io.r_last),
//     fe
//   )( 
//       List(
//       0.U -> fe,
//       1.U -> ee,
//       4.U -> fb,
//       5.U -> be
//     )
//   )

//   val bb_mux = Mux(io.w_last,fb,bb)
//   val be_mux = MuxLookup(
//     Cat(io.w_st, io.w_last, io.r_last),
//     be
//   )(
//     List(
//       0.U -> be,
//       2.U -> fe,
//       4.U -> bb,
//       6.U -> fb
//     )
//   )
//   val ee_mux = Mux(io.w_st,be,ee)

//   state := MuxLookup(
//     state,
//     ee
//   )(
//     List(
//       ff -> ff_mux,
//       fb -> fb_mux,
//       fe -> fe_mux,
//       bb -> bb_mux,
//       be -> be_mux,
//       ee -> ee_mux,
//     )
//   )

//   val w_sel = Wire(Bool())
//   w_sel := RegEnable(~w_sel,false.B, io.w_last)
//   val r_sel = Wire(Bool())
//   r_sel := RegEnable(~r_sel,false.B, io.r_last)

//   val mem = Module(new R1W1Mem(depth*2,width))
//   mem.io.wen := io.w_valid
//   mem.io.waddr := Cat(w_sel,io.w_addr)
//   mem.io.wdata := io.w_data
//   mem.io.ren := true.B
//   mem.io.raddr := Cat(r_sel,io.r_addr)
//   io.r_data := mem.io.rdata

//   io.w_ready := state===ee || state === be || state ===fe
//   io.r_ready := state === ff || state === fb || state === fe
//   // printf(p"[DataMem] state = $state, w_st = ${io.w_st}, w_last = ${io.w_last}, r_last = ${io.r_last}, w_addr = ${io.w_addr}, r_addr = ${io.r_addr}\n")
// }


// object DataMemGen extends App {
//   emitVerilog(new DataMem(16,32), Array("--target-dir", "generated"))
// }

package Softmax

import Param._

import chisel3._
import chisel3.util._


class R1W1Mem(val depth: Int, val width: Int) extends Module{
  val addrw = log2Up(depth)
  val io = IO(new  Bundle() {
    val wen = Input(Bool())
    val waddr = Input(UInt(addrw.W))
    val wdata = Input(UInt(width.W))
    val ren = Input(Bool())
    val raddr = Input(UInt(addrw.W))
    val rdata = Output(UInt(width.W))
  })
  val mem = SyncReadMem(depth, UInt(width.W))
  io.rdata := mem.read(io.raddr, io.ren)
  when(io.wen ) {
    mem.write(io.waddr, io.wdata)
  }
  // printf(p"[R1W1Mem] wen = ${io.wen}, waddr = ${io.waddr}, ren = ${io.ren}, raddr = ${io.raddr}\n")
}

class DataMem(val depth: Int, val width: Int)extends Module{
  val io = IO(new Bundle() {
    val w_st = Input(Bool())
    val w_last = Input(Bool())
    val w_data = Input(UInt(width.W))
    val w_addr = Input(UInt(log2Up(depth).W))
    val w_valid = Input(Bool())
    val w_ready = Output(Bool())

    val r_last = Input(Bool())
    val r_data = Output(UInt(width.W))
    val r_addr = Input(UInt(log2Up(depth).W))
    val r_ready = Output(Bool())
  })

  val full_cnt = Wire(UInt(3.W))
  val buzy_cnt = Wire(UInt(3.W))
  buzy_cnt := RegEnable(
    Mux(
      io.w_st,
      Mux(
        io.w_last,
        buzy_cnt,
        buzy_cnt + 1.U
      ),
      Mux(
        io.w_last,
        buzy_cnt - 1.U,
        buzy_cnt
      )
    ),
    0.U,
    io.w_st || io.w_last
  )

  full_cnt := RegEnable(
    Mux(
      io.w_last,
      Mux(
        io.r_last,
        full_cnt,
        full_cnt + 1.U
      ),
      Mux(
        io.r_last,
        full_cnt - 1.U,
        full_cnt
      )
    ),
    0.U,
    io.w_last || io.r_last
  )

  val w_sel = Wire(Bool())
  w_sel := RegEnable(~w_sel, false.B, io.w_last)
  val r_sel = Wire(Bool())
  r_sel := RegEnable(~r_sel, false.B, io.r_last)


  val mem = Module(new R1W1Mem(depth * 2, width))
  mem.io.wen := io.w_valid
  mem.io.waddr := Cat(w_sel, io.w_addr)
  mem.io.wdata := io.w_data
  mem.io.ren := true.B
  mem.io.raddr := Cat(r_sel, io.r_addr)
  io.r_data := mem.io.rdata


  io.w_ready := (full_cnt + buzy_cnt ) < 2.U
  io.r_ready := full_cnt > 0.U


}

class Mem {

}

package Linear
import Linear.Param._
import chisel3._
import chisel3.util._

class LoadWeight extends Module {
  val io = IO(new Bundle() {
    val update = Input(Bool())
    val st = Input(Bool())
    val data_in = Input(UInt((WMEM_WIDTH).W))
    val data_in_addr = Output(UInt(log2Up(WMEM_DEPTH).W))

    val data_out = Output(UInt((WMEM_WIDTH).W))
    val data_out_valid = Output(Bool())
  })

  val row_cnt = Wire(UInt(log2Up(ROW).W))
  val row_last = row_cnt === (ROW - 1).U

  val rowblock_cnt = Wire(UInt(log2Up(ROWBLOCK).W))
  val rowblock_last = rowblock_cnt === (ROWBLOCK - 1).U

  val colblock_cnt = Wire(UInt(log2Up(COLBLOCK).W))
  val colblock_last = colblock_cnt === (COLBLOCK - 1).U

  val st_idle :: st1 :: st2 ::  st_load ::Nil = Enum(4)
  
  val state = RegInit(st_idle)

  val idle_mux = Mux(io.st,st1,Mux(io.update,st_load,st_idle))
  val st1_mux = Mux(row_last ,st2,st1)
  val st2_mux = Mux(row_last ,st_idle,st2)
  val load_mux = Mux(row_last,Mux(io.update,st_load,st_idle),st_load)
  state := MuxLookup(state, st_idle)(
    List(
      st_idle -> idle_mux,
      st1 -> st1_mux,
      st2 -> st2_mux,
      st_load -> load_mux
    )
  )

  val loading = state =/=st_idle


  row_cnt := RegEnable(
    Mux(
      row_last,
      0.U,
      row_cnt + 1.U
    ),
    0.U,
    loading
  )

  rowblock_cnt := RegEnable(
    Mux(
      rowblock_last,
      0.U,
      rowblock_cnt + 1.U
    ),
    0.U,
    row_last
  )

  colblock_cnt := RegEnable(
    Mux(
      colblock_last,
      0.U,
      colblock_cnt + 1.U
    ),
    0.U,
    row_last && rowblock_last
  )

  val addr = (row_cnt + rowblock_cnt*ROW.U)*COLBLOCK.U + colblock_cnt
  io.data_in_addr := RegNext(addr)
  io.data_out_valid := RegNext(RegNext(loading,false.B),false.B)

  io.data_out := io.data_in
}


object LoadWGen extends App {
  emitVerilog(new LoadWeight, Array("--target-dir", "generated"))
}
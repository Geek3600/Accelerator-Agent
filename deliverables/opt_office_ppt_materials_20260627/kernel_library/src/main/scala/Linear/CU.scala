package Linear
import Linear._
import chisel3._
import chisel3.util._
import Linear.Param._
class CU extends Module {

  val io = IO(new Bundle() {
    val data_in = Input(UInt((MEM_WIDTH).W)) //12*8 bits
    val data_in_valid = Input(Bool())
    val data_out = Output(UInt((MEM_WIDTH).W))
    val data_out_valid = Output(Bool())

    val w_update = Output(Bool())
    val w_data = Input(UInt((WMEM_WIDTH).W))
    val w_valid = Input(Bool())

    // Prefill/Decode 模式配置
    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())
  })

  // 锁存配置
  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)

  // 计算实际批次数
  val actual_batchsize = Mux(is_prefill, seqlen, (BATCHSIZE - 1).U)


  val weight_w_sel = Wire(Bool()) 
  val weight_w_cnt = Wire(UInt(log2Up(ROW).W)) 
  val weight_w_last = weight_w_cnt === (ROW-1).U
  weight_w_sel := RegEnable(
    ~weight_w_sel,
    false.B,
    io.w_valid && weight_w_last
  )
  weight_w_cnt := RegEnable(
    Mux(
      weight_w_last,
      0.U,
      weight_w_cnt + 1.U
    ),
    0.U,
    io.w_valid
  )
  val w0 = Wire(Vec(ROW,UInt((WMEM_WIDTH).W))) 
  val w1 = Wire(Vec(ROW,UInt((WMEM_WIDTH).W)))
  val w_valids= Wire(Vec(ROW,Bool())) 

  w0(0):= RegEnable(io.w_data,io.w_valid && !weight_w_sel)
  w1(0):= RegEnable(io.w_data,io.w_valid && weight_w_sel)
  w_valids(0) := io.w_valid


  for(i <- 1 until ROW){
    w0(i):= RegEnable(w0(i-1),w_valids(i) && !weight_w_sel)
    w1(i):= RegEnable(w1(i-1),w_valids(i) && weight_w_sel)
    w_valids(i) := RegNext(w_valids(i - 1),false.B)
  }


  val weight_r_sel = Wire(Bool())
  val weight  = Wire (Vec(ROW,Vec(COL, UInt((DATAW).W))))
  for(i <- 0 until ROW){
    for( j <- 0 until COL){
      weight(i)(j) := Mux(weight_r_sel,w0(i)((j+1)*DATAW - 1,j*DATAW),w1(i)((j+1)*DATAW - 1,j*DATAW))
    }
  }


  val batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val batchsize_last = batchsize_cnt === actual_batchsize
  batchsize_cnt := RegEnable(
    Mux(
      batchsize_last,
      0.U,
      batchsize_cnt + 1.U
    ),
    0.U,
    io.data_in_valid
  )

  val block_cnt = Wire(UInt(log2Up(ROWBLOCK).W))
  val block_last = block_cnt === (ROWBLOCK - 1).U
  block_cnt := RegEnable(
    Mux(
      block_last,
      0.U,
      block_cnt + 1.U
    ),
    0.U,
    batchsize_last && io.data_in_valid
  )


  val input_delay = 2
  val indata_pipreg = Module(new PipReg(input_delay,MEM_WIDTH))
  val invalid_pipreg = Module(new PipReg(input_delay,1))
  indata_pipreg.io.in := io.data_in
  invalid_pipreg.io.in := io.data_in_valid


  val batchsizelast_pipreg = Module(new PipReg(input_delay,1))
  batchsizelast_pipreg.io.in := batchsize_last

  weight_r_sel := RegEnable(
    ~weight_r_sel,
    false.B,
    batchsizelast_pipreg.io.out.asBool
  )
  io.w_update := batchsize_last



  val mul_list = List.fill(ROW)(List.fill(COL)(Module(new  Multiplier)))
  for(i <- 0 until ROW){
    for(j <- 0 until COL){
      mul_list(i)(j).io.in0 := indata_pipreg.io.out(DATAW*(i+1)- 1,DATAW*i)
      mul_list(i)(j).io.in1 := weight(i)(j)
    }
  }
  val mul_delay = 1
 
  val addTreeList = List.fill(COL)(Module(new AddTree(ROW)))
  for(j <- 0 until COL){
    for(i <- 0 until ROW){
      addTreeList(j).io.ins(i):= mul_list(i)(j).io.out

    }
  }
  val add_delay = log2Up(ROW)


  val psums0 = Wire(Vec(BATCHSIZE,Vec(COL,UInt(DATAW.W))))
  val psums1 = Wire(Vec(BATCHSIZE,Vec(COL,UInt(DATAW.W))))

  val block_first = block_cnt === 0.U
  val psum_last = block_last && batchsize_last
  val block_first_pipreg = Module(new PipReg(input_delay  + mul_delay +add_delay  ,1))
  val cnt_batchsize_pipreg = Module(new PipReg(input_delay  + mul_delay +add_delay  ,batchsize_cnt.getWidth))
  val psum_valid_pipreg = Module(new PipReg(input_delay  + mul_delay +add_delay  ,1))
  val psum_last_pipreg = Module(new PipReg(input_delay  + mul_delay +add_delay  ,1))
  block_first_pipreg.io.in := block_first
  cnt_batchsize_pipreg.io.in := batchsize_cnt
  psum_valid_pipreg.io.in := io.data_in_valid
  psum_last_pipreg.io.in := psum_last



  val block_first_pipout = block_first_pipreg.io.out.asBool
  val cnt_batchsize_pipout = cnt_batchsize_pipreg.io.out
  val psum_valid_pipout = psum_valid_pipreg.io.out.asBool
  val psum_last_pipout = psum_last_pipreg.io.out.asBool
  val psum_sel = Wire(Bool())
  psum_sel := RegEnable(
    ~psum_sel,
    false.B,
    psum_valid_pipout && psum_last_pipout
  )


  for(i <- 0 until BATCHSIZE){
    for(j <- 0 until  COL){
      psums0(i)(j) := RegEnable(
        Mux(
          block_first_pipout,
          addTreeList(j).io.out,
          addTreeList(j).io.out + psums0(i)(j)
        ),
        0.U,
        cnt_batchsize_pipout === i.U && psum_valid_pipout && !psum_sel
      )

      psums1(i)(j) := RegEnable(
        Mux(
          block_first_pipout,
          addTreeList(j).io.out,
          addTreeList(j).io.out + psums1(i)(j)
        ),
        0.U,
        cnt_batchsize_pipout === i.U && psum_valid_pipout && psum_sel
      )

    }


  }



  val res_sel = !psum_sel

  val send_st = psum_last_pipout
  val res_vector_num = (COL + ROW - 1)/ROW
  val res_vector_cnt = Wire(UInt(log2Up(res_vector_num).W))
  val res_vector_last = res_vector_cnt ===  (res_vector_num- 1).U
  val res_batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val res_batchsize_last = res_batchsize_cnt === actual_batchsize

  val idle :: buzy :: Nil = Enum(2)
  val state = RegInit(idle)
  val is_idle = state === idle
  val is_buzy = state === buzy
  val idle_mux = Mux(send_st,buzy,idle)
  val res_done= res_batchsize_last && res_vector_last
  val buzy_mux = Mux(

    res_done,
    Mux(
      send_st,
      buzy,
      idle
      
    ),
    buzy
  )
  state := Mux(is_idle,idle_mux,buzy_mux)



  res_batchsize_cnt := RegEnable(
    Mux(
      res_batchsize_last,
      0.U,
      res_batchsize_cnt + 1.U
    ),
    0.U,
    is_buzy
  )


  res_vector_cnt := RegEnable(
    Mux(
      res_vector_last,
      0.U,
      res_vector_cnt + 1.U
    ),
    0.U,
    is_buzy && res_batchsize_last
  )


  val psum0_token = MuxLookup(res_batchsize_cnt, 0.U)(
    (0 until BATCHSIZE).map{i => {
      i.U ->Cat( psums0(i).reverse)
    }}
  )


  val psum1_token = MuxLookup(res_batchsize_cnt, 0.U)(
    (0 until BATCHSIZE).map { i => {
      i.U -> Cat( psums1(i).reverse)
    }
    }
  )

  val psum_batch =Mux(RegNext(res_sel),RegNext(psum1_token),RegNext(psum0_token))
  val psum_res = MuxLookup(RegNext(res_vector_cnt), psum_batch(MEM_WIDTH-1,0))(
    (0 until res_vector_num).map{ i =>{
      i.U -> psum_batch((i + 1)*MEM_WIDTH-1,i*MEM_WIDTH)
    }

    }
  )

  io.data_out:= psum_res

  val res_delay = 1
  val res_valid_pipreg = Module(new PipReg(res_delay,1))
  res_valid_pipreg.io.in := is_buzy


  io.data_out_valid := res_valid_pipreg.io.out.asBool


}

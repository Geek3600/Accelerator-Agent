package QKVLinear

import QKVLinear.Param._
import QuantCommon.DspHints
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class SignedMultiplierInt8 extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(SInt(DATAW.W))
    val in1 = Input(SInt(DATAW.W))
    val out = Output(SInt(16.W))
  })

  io.out := RegNext(io.in0 * io.in1)
}

class SignedAddTree32(val num: Int) extends Module {
  val io = IO(new Bundle() {
    val ins = Input(Vec(num, SInt(16.W)))
    val out = Output(SInt(INT32_WIDTH.W))
  })

  def recTree(vals: Seq[SInt]): SInt = {
    if (vals.length == 1) vals.head
    else {
      val next = vals.grouped(2).map {
        case Seq(a, b) => RegNext((a +& b).asSInt)
        case Seq(a) => RegNext(a)
      }.toSeq
      recTree(next)
    }
  }

  io.out := recTree(io.ins)
}

class SignedMacChain32(val num: Int) extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(Vec(num, SInt(DATAW.W)))
    val in1 = Input(Vec(num, SInt(DATAW.W)))
    val out = Output(SInt(INT32_WIDTH.W))
  })

  DspHints.preferDsp(this)
  val acc = Reg(Vec(num, SInt(INT32_WIDTH.W)))
  for (i <- 0 until num) {
    DspHints.preferDsp(acc(i))
  }
  val alignedIn0 = Wire(Vec(num, SInt(DATAW.W)))
  val alignedIn1 = Wire(Vec(num, SInt(DATAW.W)))
  for (i <- 0 until num) {
    if (i == 0) {
      alignedIn0(i) := io.in0(i)
      alignedIn1(i) := io.in1(i)
    } else {
      alignedIn0(i) := ShiftRegister(io.in0(i), i)
      alignedIn1(i) := ShiftRegister(io.in1(i), i)
    }
  }

  // Keep the MAC chain unreset so Vivado can map it onto DSP cascade logic.
  // Each stage consumes the aligned operand from the same logical block as the
  // incoming accumulated partial sum; otherwise consecutive blocks get mixed.
  acc(0) := (alignedIn0(0) * alignedIn1(0)).asSInt
  for (i <- 1 until num) {
    val stageSum = Wire(SInt(INT32_WIDTH.W))
    stageSum := (acc(i - 1) +& (alignedIn0(i) * alignedIn1(i)).asSInt).asSInt
    acc(i) := stageSum
  }
  io.out := acc(num - 1)
}

class CUQuant extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())
    val data_out = Output(UInt((ROW * INT32_WIDTH).W))
    val data_out_valid = Output(Bool())

    val w_update = Output(Bool())
    val w_data = Input(Vec(ROW, UInt(WMEM_WIDTH.W)))
    val w_data_sel = Input(Bool())
    val w_valid = Input(Bool())

    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())
  })

  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)
  val is_single_query = RegEnable(io.cfg_single_query, false.B, io.cfg_valid)
  val decode_batch_last = Mux(is_single_query, 0.U(log2Up(BATCHSIZE).W), (BATCHSIZE - 1).U)
  val actual_batchsize = Mux(is_prefill, seqlen, decode_batch_last)
  val colFanoutGroupSize = 6
  val colFanoutGroups = (COL + colFanoutGroupSize - 1) / colFanoutGroupSize

  val w0 = Reg(Vec(ROW, UInt(WMEM_WIDTH.W)))
  val w1 = Reg(Vec(ROW, UInt(WMEM_WIDTH.W)))
  when(io.w_valid && !io.w_data_sel) {
    w0 := io.w_data
  }
  when(io.w_valid && io.w_data_sel) {
    w1 := io.w_data
  }

  val weight_r_sel = RegInit(false.B)
  dontTouch(weight_r_sel)
  val selectedWeightRows = Wire(Vec(ROW, UInt(WMEM_WIDTH.W)))
  val weight = Wire(Vec(ROW, Vec(COL, SInt(DATAW.W))))
  for (i <- 0 until ROW) {
    selectedWeightRows(i) := Mux(weight_r_sel, w1(i), w0(i))
  }
  for (i <- 0 until ROW) {
    for (j <- 0 until COL) {
      weight(i)(j) := selectedWeightRows(i)((j + 1) * DATAW - 1, j * DATAW).asSInt
    }
  }

  val batchsizeCntReg = RegInit(0.U(log2Up(BATCHSIZE).W))
  val batchsize_cnt = batchsizeCntReg
  val batchsize_last = batchsize_cnt === actual_batchsize
  when(io.data_in_valid) {
    batchsizeCntReg := Mux(batchsize_last, 0.U, batchsizeCntReg + 1.U)
  }

  val blockCntReg = RegInit(0.U(log2Up(ROWBLOCK).W))
  val block_cnt = blockCntReg
  val block_last = block_cnt === (ROWBLOCK - 1).U
  when(batchsize_last && io.data_in_valid) {
    blockCntReg := Mux(block_last, 0.U, blockCntReg + 1.U)
  }

  val input_delay = 2
  val indata_pipreg = Module(new PipReg(input_delay, MEM_WIDTH))
  indata_pipreg.io.in := io.data_in

  val batchsizeFirst = batchsize_cnt === 0.U
  val weightUpdateReg = RegNext(io.data_in_valid && batchsizeFirst, false.B)
  io.w_update := weightUpdateReg

  // Switch to the next weight tile only after the last token of the current
  // batch has fully exited the input alignment pipeline. Toggling one cycle
  // too early corrupts the current block's MAC accumulation.
  val weightSelLatency = input_delay + 1
  val weightSelPipe = RegInit(VecInit(Seq.fill(weightSelLatency)(false.B)))
  val weightSelValidPipe = RegInit(VecInit(Seq.fill(weightSelLatency)(false.B)))
  weightSelPipe(0) := io.w_data_sel
  weightSelValidPipe(0) := io.w_valid
  for (i <- 1 until weightSelLatency) {
    weightSelPipe(i) := weightSelPipe(i - 1)
    weightSelValidPipe(i) := weightSelValidPipe(i - 1)
  }
  when(weightSelValidPipe.last) {
    weight_r_sel := weightSelPipe.last
  }

  val inputLaneReplicas = Seq.tabulate(ROW, colFanoutGroups) { (i, _) =>
    val laneReplica = Wire(SInt(DATAW.W))
    laneReplica := indata_pipreg.io.out(DATAW * (i + 1) - 1, DATAW * i).asSInt
    dontTouch(laneReplica)
    laneReplica
  }

  val macChainList = List.fill(COL)(Module(new SignedMacChain32(ROW)))
  for (j <- 0 until COL) {
    for (i <- 0 until ROW) {
      macChainList(j).io.in0(i) := inputLaneReplicas(i)(j / colFanoutGroupSize)
      macChainList(j).io.in1(i) := weight(i)(j)
    }
  }
  val macLatency = ROW

  // These partial sums are fully overwritten on the first block of each token
  // before they are observed, so datapath reset only hurts packing density.
  val psums0 = Reg(Vec(BATCHSIZE, Vec(COL, SInt(INT32_WIDTH.W))))
  val psums1 = Reg(Vec(BATCHSIZE, Vec(COL, SInt(INT32_WIDTH.W))))

  val block_first = block_cnt === 0.U
  val psum_last = block_last && batchsize_last
  // The MAC chain result emerges one cycle later than the raw input-delay +
  // accumulator-depth estimate because the chain state is observed after the
  // registered stage update. Keep the metadata aligned to the committed MAC
  // result, not the combinational inputs.
  val psumMetaLatency = input_delay + macLatency + 2
  val blockFirstLatency = psumMetaLatency + 1
  val block_first_pipreg = Module(new PipReg(blockFirstLatency, 1))
  val cnt_batchsize_pipreg = Module(new PipReg(psumMetaLatency, batchsize_cnt.getWidth))
  val psum_valid_pipreg = Module(new PipReg(psumMetaLatency, 1))
  val psum_last_pipreg = Module(new PipReg(psumMetaLatency, 1))
  block_first_pipreg.io.in := block_first
  cnt_batchsize_pipreg.io.in := batchsize_cnt
  psum_valid_pipreg.io.in := io.data_in_valid
  psum_last_pipreg.io.in := (psum_last && io.data_in_valid).asUInt

  val block_first_pipout = block_first_pipreg.io.out.asBool
  val cnt_batchsize_pipout = cnt_batchsize_pipreg.io.out
  val psum_valid_pipout = psum_valid_pipreg.io.out.asBool
  val psum_last_pipout = psum_last_pipreg.io.out.asBool
  val psumSelReg = RegInit(false.B)
  val psum_sel = psumSelReg
  when(psum_valid_pipout && psum_last_pipout) {
    psumSelReg := !psumSelReg
  }

  for (i <- 0 until BATCHSIZE) {
    for (j <- 0 until COL) {
      when(cnt_batchsize_pipout === i.U && psum_valid_pipout && !psum_sel) {
        psums0(i)(j) := Mux(block_first_pipout, macChainList(j).io.out, psums0(i)(j) + macChainList(j).io.out)
      }
      when(cnt_batchsize_pipout === i.U && psum_valid_pipout && psum_sel) {
        psums1(i)(j) := Mux(block_first_pipout, macChainList(j).io.out, psums1(i)(j) + macChainList(j).io.out)
      }
    }
  }

  val send_st = psum_last_pipout
  val out_bank_sel = RegInit(false.B)
  when(send_st) {
    out_bank_sel := psum_sel
  }
  val res_vector_num = (COL + ROW - 1) / ROW
  val resVectorCntReg = RegInit(0.U(log2Up(res_vector_num).W))
  val res_vector_cnt = resVectorCntReg
  val res_vector_last = res_vector_cnt === (res_vector_num - 1).U
  val resBatchsizeCntReg = RegInit(0.U(log2Up(BATCHSIZE).W))
  val res_batchsize_cnt = resBatchsizeCntReg
  val res_batchsize_last = res_batchsize_cnt === actual_batchsize

  val idle :: buzy :: Nil = Enum(2)
  val state = RegInit(idle)
  val is_idle = state === idle
  val is_buzy = state === buzy
  val idle_mux = Mux(send_st, buzy, idle)
  val res_done = res_batchsize_last && res_vector_last
  val buzy_mux = Mux(res_done, Mux(send_st, buzy, idle), buzy)
  state := Mux(is_idle, idle_mux, buzy_mux)

  when(is_buzy) {
    resBatchsizeCntReg := Mux(res_batchsize_last, 0.U, resBatchsizeCntReg + 1.U)
    when(res_batchsize_last) {
      resVectorCntReg := Mux(res_vector_last, 0.U, resVectorCntReg + 1.U)
    }
  }

  val psum0_token = MuxLookup(res_batchsize_cnt, 0.U((COL * INT32_WIDTH).W))(
    (0 until BATCHSIZE).map { i => i.U -> Cat(psums0(i).reverse.map(_.asUInt)) }
  )
  val psum1_token = MuxLookup(res_batchsize_cnt, 0.U((COL * INT32_WIDTH).W))(
    (0 until BATCHSIZE).map { i => i.U -> Cat(psums1(i).reverse.map(_.asUInt)) }
  )

  val psum_batch = RegNext(Mux(out_bank_sel, psum1_token, psum0_token), 0.U((COL * INT32_WIDTH).W))
  val psum_vector_sel_d1 = RegNext(res_vector_cnt, 0.U(res_vector_cnt.getWidth.W))
  val psum_vector_sel = RegNext(psum_vector_sel_d1, 0.U(res_vector_cnt.getWidth.W))
  val psum_res_int = MuxLookup(psum_vector_sel, psum_batch(ROW * INT32_WIDTH - 1, 0))(
    (0 until res_vector_num).map { i =>
      i.U -> psum_batch((i + 1) * ROW * INT32_WIDTH - 1, i * ROW * INT32_WIDTH)
    }
  )

  io.data_out := psum_res_int
  io.data_out_valid := RegNext(RegNext(is_buzy, false.B), false.B)
}

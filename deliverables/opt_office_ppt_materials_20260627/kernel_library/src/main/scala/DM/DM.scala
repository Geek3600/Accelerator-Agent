package DM

import DM.Param._
import chisel3._
import chisel3.util._

class DMCUPlus extends Module {

  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W)) //prefill的时候表示的是prompt的token长度，decode的时候表示的是当前已生成序列的长度
    //    val cfg_prelen = Input(UInt(log2Up(MAX_PREFILL).W)) //prefill 长度减去1
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool()) // 外部配置有效信号

    val data_in = Input(UInt((LOAD_VECNUM * DATAW * 2).W)) //每周期输入两个Q和K元素 [k1,k0,q1,q0]
    val data_in_valid = Input(Bool()) // 输入有效

    val data_out = Output(UInt((MAX_SEQLEN * DATAW * 4).W)) // 输出的26个点积结果，每个结果预留 32 位，实际用 8 位
    val data_out_valid = Output(Bool()) // 输出有效
  })
  val is_prefill = RegEnable(io.cfg_prefill, io.cfg_valid) // 是否是prefill模式，会锁存，直到下一个cfg_valid
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid) //  prefill的时候表示的是prompt的token长度，decode的时候表示的是当前已生成序列的长度

  //  一个 HEAD_VECNUM 维的向量，每次加载 LOAD_VECNUM 个元素，需要 headvec_num 次
  val headvec_num = HEAD_VECNUM / LOAD_VECNUM // 每个注意力头维度是64，每次加载两个元素，所以需要加载32次，需要累积满64个元素才能组成一个向量进行计算
  val headvec_cnt = Wire(UInt(log2Up(headvec_num).W)) // 累计计数器，表示当前已经收集了多少个元素
  val headvec_last = headvec_cnt === (headvec_num - 1).U // 表示是否已经收集满64个元素
  headvec_cnt := RegEnable(
    Mux(
      headvec_last,
      0.U,
      headvec_cnt + 1.U
    ),
    0.U,
    io.data_in_valid // 只要输入有效，就马上开始收集数据
  )

  val in_q = io.data_in(LOAD_VECNUM * DATAW - 1, 0) // 输入数据低位是Q
  val in_k = io.data_in(LOAD_VECNUM * DATAW * 2 - 1, LOAD_VECNUM * DATAW) // 高位是K

  val QVec = Wire(Vec(HEAD_VECNUM / LOAD_VECNUM, UInt((LOAD_VECNUM * DATAW).W))) // 用于收集64个Q元素
  val KVec = Wire(Vec(HEAD_VECNUM / LOAD_VECNUM, UInt((LOAD_VECNUM * DATAW).W))) // 用于收集64个K元素

  for (i <- 0 until HEAD_VECNUM / LOAD_VECNUM) { // 对输入数据的QK进行拼接，等待凑齐64个元素
    QVec(i) := RegEnable(in_q, io.data_in_valid && headvec_cnt === i.U)
    KVec(i) := RegEnable(in_k, io.data_in_valid && headvec_cnt === i.U)
  }

  // headvec_last 表示是否已经收集满64个元素
  // QKVec_valid 在完整向量收集完毕的下一个周期有效，用于触发 Cache 写入
  val QKVec_valid = RegNext(headvec_last && io.data_in_valid, false.B) 

  // 下面两个计数器用于区分不同模式下的向量收集进度
  val prefill_cnt = Wire(UInt(MAX_PREFILL.W)) // prefill状态下，N的计数器，用于生成Cache的写入地址
  val prefill_last = prefill_cnt === seqlen // prefill模式下，表示已经收集满了seqlen个64维向量
  prefill_cnt := RegEnable(
    Mux(
      prefill_last,
      0.U,
      prefill_cnt + 1.U
    ),
    QKVec_valid && is_prefill
  )

  // val batch_cnt = Wire(UInt(log2Up(BATCHSIZE).W)) // decode状态下，B的计数器，用于生成Cache的写入地址
  // val batch_last = batch_cnt === (BATCHSIZE - 1).U // decode模式下，表示已经收集满了BATCHSIZE个64维向量
  // batch_cnt := RegEnable(
  //   Mux(
  //     batch_last,
  //     0.U,
  //     batch_cnt + 1.U
  //   ),
  //   QKVec_valid && (!is_prefill || prefill_last)
  // )

  // large batch计数器，用于Kcache的地址生成，每个 lbatch 在 KCache 中占用 MAX_SEQLEN=26 个地址
  val lbatch_cnt = Wire(UInt(log2Up(LBATCHSIZE).W)) // 由于我们要在片上加kvcache，一个batch内v的不同用户要写道不同地址；不同batch的v也要写到不同地址，所以需要一个计数器，我们称其为large batch
  val lbatch_last = lbatch_cnt === (LBATCHSIZE - 1).U
  lbatch_cnt := RegEnable(
    Mux(
      lbatch_last,
      0.U,
      lbatch_cnt + 1.U
    ),
    0.U,
    QKVec_valid && (!is_prefill || prefill_last)
  )


  // KCache 地址布局：
  // 地址范围          内容
  // ─────────────────────────────
  // 0-25             lbatch 0 的 K 历史 (最多26个token)
  // 26-51            lbatch 1 的 K 历史
  // 52-77            lbatch 2 的 K 历史
  // ...
  // 3302-3327        lbatch 127 的 K 历史


  val QCache = Module(new R1W1Mem(MAX_PREFILL , HEAD_VECNUM * DATAW)) //qkcache及其的写
  val KCache = Module(new R1W1Mem(LBATCHSIZE * MAX_SEQLEN, HEAD_VECNUM * DATAW)) // KCache的存储深度是LBATCHSIZE * MAX_SEQLEN：MAX_SEQLEN是最大的序列长度26，也就是每个历史K的N最大值就是26，LBATCHSIZE则表示，每个数据的宽度是一个头维度的向量


  QCache.io.wen := QKVec_valid // QCache写使能
  QCache.io.wdata := QVec.asUInt // QCache写数据
  // Prefill: 写地址 0,1,2,...,seqlen
  // Decode:  总是写地址 0（只有1个新Q）
  QCache.io.waddr := Mux(is_prefill, prefill_cnt, 0.U) // QCache写地址，每次写入一个长度为HEAD_VECNUM的向量


  KCache.io.wen := QKVec_valid   // KCache写使能
  KCache.io.wdata := KVec.asUInt // KCache写数据
  // 进行完prefill后，Kcache已经写到seqlen的位置，后续的decode阶段则是继续追加到seqlen的位置
  KCache.io.waddr := Mux(is_prefill, 
      lbatch_cnt * MAX_SEQLEN.U + prefill_cnt,   // Prefill: 顺序写入，0, 1, 2, ..., seqlen
      lbatch_cnt * MAX_SEQLEN.U + seqlen         // Decode: 追加到序列末尾，追加到seqlen的位置
    ) // KCache写地址


  val st_load :: st_compute :: Nil = Enum(2) // 状态机，load状态往cache写数据，compute状态读数据计算
  val compute_over = Wire(Bool()) //todo
  val state = RegInit(st_load)
  val is_comp = state === st_compute
  val load_mux = Mux(
    QKVec_valid && (!is_prefill || prefill_last), // load -> compute状态转化的条件：1.如果是decode阶段，则马上转换，2.如果是prefill阶段，则需要等所有token的QK收集完
    st_compute,
    st_load
  )
  state := Mux(
    state === st_load,
    load_mux,
    Mux(
      compute_over, // 如果计算完成，就转换到load状态
      load_mux,
      st_compute
    )
  )

  val lbatch_cnt_r = RegEnable(lbatch_cnt, QKVec_valid && (!is_prefill || prefill_last)) // 读kcache的地址相关的寄存器

  // 计算 Q·K 点积需要三层循环 = 三层计数器：用于生成QKCache的读地址
  // for comp_prefill_q_cnt in 0..seqlen:      # 外层：遍历每个Q（仅Prefill）
  //   for comp_key_cnt in 0..seqlen:          # 中层：遍历每个K
  //     for comp_headv_cnt in 0..1:           # 内层：64维分2批计算
  //       计算部分点积
  val comp_headv_cnt = Wire(UInt(log2Up(HEAD_VECNUM / MULNUM).W)) // compote状态的控制计数器。一个q和k相乘时，序列长度可能比乘法器数量多，用comp_headv_cnt进行多次乘法；一个q要和多个k相乘，用comp_key_cnt控制；prefill过程有多个q参与计算，用comp_prefill_q_cnt控制。
  val comp_headv_last = comp_headv_cnt === (HEAD_VECNUM / MULNUM - 1).U
  comp_headv_cnt := RegEnable( // 内层循环，每周期递增
    Mux(
      comp_headv_last,
      0.U,
      comp_headv_cnt + 1.U
    ),
    0.U,
    is_comp
  )

  val comp_key_cnt = Wire(UInt(log2Up(MAX_SEQLEN).W))
  val comp_key_last = comp_key_cnt === seqlen
  comp_key_cnt := RegEnable( // 中层：内层完成后递增
    Mux(
      comp_key_last,
      0.U,
      comp_key_cnt + 1.U
    ),
    0.U,
    is_comp && comp_headv_last
  )

  val comp_prefill_q_cnt = Wire(UInt(log2Up(MAX_PREFILL).W))
  val comp_prefill_q_last = comp_prefill_q_cnt === seqlen
  comp_prefill_q_cnt := RegEnable( // 外层：中层完成后递增（仅Prefill）
    Mux(
      comp_prefill_q_last,
      0.U,
      comp_prefill_q_cnt + 1.U
    ),
    0.U,
    is_comp && comp_headv_last && comp_key_last && is_prefill // 在decode时不递增，因为只有1个新Q
  )


  compute_over := comp_headv_last && comp_key_last && (comp_prefill_q_last || !is_prefill) // 计算状态结束信号

  QCache.io.ren := is_comp // QKcache读
  QCache.io.raddr := Mux(is_prefill,  comp_prefill_q_cnt, 0.U) // Prefill: 读地址 0,1,2,...,seqlen；Decode: 读地址 0（只有1个新Q）

  KCache.io.ren := is_comp
  KCache.io.raddr := lbatch_cnt_r * MAX_SEQLEN.U + comp_key_cnt

  // 64维向量分成两片，每片 32 维，因为乘法器数量不够，只有32个
  val Q_Sel = MuxLookup( // 如前面所说”一个q和k相乘时，序列长度可能比乘法器数量多，用comp_headv_cnt进行多次乘法”，这里就是在选择不同的子向量进行相乘
    RegNext(comp_headv_cnt), // 根据计数器的值进行选择
    0.U
  )(
    (0 until HEAD_VECNUM / MULNUM).map { i => i.U -> QCache.io.rdata((i + 1) * MULNUM * DATAW - 1, i * MULNUM * DATAW) } // 生成地址
  )
  val K_Sel = MuxLookup(
    RegNext(comp_headv_cnt),
    0.U
  )(
    (0 until HEAD_VECNUM / MULNUM).map { i => i.U -> KCache.io.rdata((i + 1) * MULNUM * DATAW - 1, i * MULNUM * DATAW) }
  )

  // 乘法器阵列，32个8位乘法器
  val mullist = List.fill(MULNUM)(Module(new Multiplier(DATAW))) // 乘加过程
  //乘法器内部会打两拍
  for (i <- 0 until MULNUM) { 
    mullist(i).io.in0 := Q_Sel((i + 1) * DATAW - 1, i * DATAW)
    mullist(i).io.in1 := K_Sel((i + 1) * DATAW - 1, i * DATAW)
  }

  // 加法树
  val addtree = Module(new AddTree(MULNUM, DATAW * 2))
  for (i <- 0 until MULNUM) {
    addtree.io.ins(i) := mullist(i).io.out
  }
  //加法树，打log拍
  val acc_first = comp_headv_cnt === 0.U // 第一批
  val acc_first_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM), 1)) // 延迟8周期对齐
  acc_first_pipreg.io.in := acc_first.asUInt

  val acc_update = is_comp // 累加器的初始以及更新
  val acc_update_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM), 1))
  acc_update_pipreg.io.in := acc_update.asUInt

  val acc_reg = Wire(UInt(DATAW.W))
  acc_reg := RegEnable(
    Mux(
      acc_first_pipreg.io.out.asBool,
      addtree.io.out,  // 第一批：直接赋值
      addtree.io.out + acc_reg // 第二批：累加
    ),
    0.U,
    acc_update_pipreg.io.out.asBool
  )
  // 结果收集
  val res_cache = Wire(Vec(MAX_SEQLEN, UInt(DATAW.W))) // res的拼接，26个结果槽位
  val acc_valid = comp_headv_last && is_comp
  val acc_valid_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM) + 1, 1))
  acc_valid_pipreg.io.in := acc_valid

  val res_ksel = comp_key_cnt
  val res_ksel_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM) + 1, log2Up(MAX_SEQLEN)))
  res_ksel_pipreg.io.in := res_ksel

  for (i <- 0 until MAX_SEQLEN) {
    res_cache(i) := RegEnable(acc_reg, acc_valid_pipreg.io.out.asBool && res_ksel_pipreg.io.out === i.U)
  }

  val res_valid = RegNext(res_ksel_pipreg.io.out === seqlen && acc_valid_pipreg.io.out.asBool, false.B)


  io.data_out := res_cache.asUInt
  io.data_out_valid := res_valid


}

//  DM 模块工作流程详解

//   一、首先明确几个关键参数

//   HEAD_VECNUM = 64      → 一个Q/K向量有64个元素
//   LOAD_VECNUM = 2       → 每周期从Load0收到2个Q元素+2个K元素
//   MULNUM = 32           → 有32个乘法器
//   MAX_SEQLEN = 26       → 最大序列长度26
//   MAX_PREFILL = 8       → Prefill最多8个token

//   ---
//   二、数据收集阶段（Load 阶段）

//   问题：一个完整的 Q/K 向量怎么收集？

//   每周期只收到 2 个元素，但一个向量有 64 个元素，所以需要 32 个周期 才能收集完一个完整向量。

//   周期0:  收到 [q1,q0], [k1,k0]     → 存入 QVec(0), KVec(0)
//   周期1:  收到 [q3,q2], [k3,k2]     → 存入 QVec(1), KVec(1)
//   周期2:  收到 [q5,q4], [k5,k4]     → 存入 QVec(2), KVec(2)
//   ...
//   周期31: 收到 [q63,q62], [k63,k62] → 存入 QVec(31), KVec(31)
//   周期32: QKVec_valid = 1，向量收集完毕！

//   收集完毕后：
//   - QVec 包含完整的 64 维 Q 向量
//   - KVec 包含完整的 64 维 K 向量
//   - 触发写入 Cache

//   ---
//   三、Prefill 模式完整流程

//   假设 seqlen = 2，即有 3 个 token（token0, token1, token2）

//   阶段1：收集所有 token 的 Q 和 K

//   ┌─────────────────────────────────────────────────────────────────┐
//   │                    Load 阶段（收集数据）                          │
//   ├─────────────────────────────────────────────────────────────────┤
//   │                                                                 │
//   │  周期 0-31:   收集 Token0 的 Q0 和 K0                            │
//   │              ↓                                                  │
//   │  周期 32:    QKVec_valid=1                                      │
//   │              写入 QCache[0] = Q0                                │
//   │              写入 KCache[0] = K0                                │
//   │              prefill_cnt: 0→1                                   │
//   │                                                                 │
//   │  周期 33-64: 收集 Token1 的 Q1 和 K1                            │
//   │              ↓                                                  │
//   │  周期 65:    QKVec_valid=1                                      │
//   │              写入 QCache[1] = Q1                                │
//   │              写入 KCache[1] = K1                                │
//   │              prefill_cnt: 1→2                                   │
//   │                                                                 │
//   │  周期 66-97: 收集 Token2 的 Q2 和 K2                            │
//   │              ↓                                                  │
//   │  周期 98:    QKVec_valid=1, prefill_last=1                      │
//   │              写入 QCache[2] = Q2                                │
//   │              写入 KCache[2] = K2                                │
//   │              prefill_cnt: 2→0 (回零)                            │
//   │              状态转换: st_load → st_compute                      │
//   │                                                                 │
//   └─────────────────────────────────────────────────────────────────┘

//   Load 阶段结束后 Cache 状态：

//   QCache (深度8，宽度512位):
//   ┌─────────┬─────────────────────────────────┐
//   │ 地址    │ 内容                             │
//   ├─────────┼─────────────────────────────────┤
//   │   0     │ Q0 = [q0_0, q0_1, ..., q0_63]   │
//   │   1     │ Q1 = [q1_0, q1_1, ..., q1_63]   │
//   │   2     │ Q2 = [q2_0, q2_1, ..., q2_63]   │
//   │  3-7    │ (未使用)                         │
//   └─────────┴─────────────────────────────────┘

//   KCache (深度3328，宽度512位):
//   ┌─────────┬─────────────────────────────────┐
//   │ 地址    │ 内容                             │
//   ├─────────┼─────────────────────────────────┤
//   │   0     │ K0 = [k0_0, k0_1, ..., k0_63]   │
//   │   1     │ K1 = [k1_0, k1_1, ..., k1_63]   │
//   │   2     │ K2 = [k2_0, k2_1, ..., k2_63]   │
//   │  3-25   │ (未使用，预留给后续decode)        │
//   │  26-51  │ (lbatch=1 的区域)                │
//   │  ...    │ ...                             │
//   └─────────┴─────────────────────────────────┘

//   阶段2：计算所有 Q·K 点积

//   Prefill 需要计算完整的注意力矩阵：

//   需要计算的点积:
//           K0      K1      K2
//   Q0    Q0·K0   Q0·K1   Q0·K2
//   Q1    Q1·K0   Q1·K1   Q1·K2
//   Q2    Q2·K0   Q2·K1   Q2·K2

//   三层循环结构：

//   for q_idx in 0..2:           // comp_prefill_q_cnt: 遍历每个Q
//     for k_idx in 0..2:         // comp_key_cnt: 遍历每个K
//       for part in 0..1:        // comp_headv_cnt: 64维分2批
//         计算部分点积

//   详细计算过程：

//   ┌─────────────────────────────────────────────────────────────────┐
//   │                  Compute 阶段（计算点积）                         │
//   ├─────────────────────────────────────────────────────────────────┤
//   │                                                                 │
//   │ ═══════════════ 计算 Q0 与所有 K 的点积 ═══════════════          │
//   │                                                                 │
//   │ comp_prefill_q_cnt = 0, 读取 QCache[0] = Q0                     │
//   │                                                                 │
//   │   comp_key_cnt=0, 读取 KCache[0] = K0                           │
//   │     comp_headv_cnt=0: Q0[0:31] × K0[0:31] → 部分和1             │
//   │     comp_headv_cnt=1: Q0[32:63] × K0[32:63] → 部分和2           │
//   │     acc_reg = 部分和1 + 部分和2 = Q0·K0 ✓                       │
//   │     → 存入 res_cache[0]                                         │
//   │                                                                 │
//   │   comp_key_cnt=1, 读取 KCache[1] = K1                           │
//   │     comp_headv_cnt=0: Q0[0:31] × K1[0:31] → 部分和1             │
//   │     comp_headv_cnt=1: Q0[32:63] × K1[32:63] → 部分和2           │
//   │     acc_reg = Q0·K1 ✓                                           │
//   │     → 存入 res_cache[1]                                         │
//   │                                                                 │
//   │   comp_key_cnt=2, 读取 KCache[2] = K2                           │
//   │     comp_headv_cnt=0: Q0[0:31] × K2[0:31] → 部分和1             │
//   │     comp_headv_cnt=1: Q0[32:63] × K2[32:63] → 部分和2           │
//   │     acc_reg = Q0·K2 ✓                                           │
//   │     → 存入 res_cache[2]                                         │
//   │     → res_valid = 1, 输出 [Q0·K2, Q0·K1, Q0·K0]                 │
//   │                                                                 │
//   │ ═══════════════ 计算 Q1 与所有 K 的点积 ═══════════════          │
//   │                                                                 │
//   │ comp_prefill_q_cnt = 1, 读取 QCache[1] = Q1                     │
//   │   (重复上述过程...)                                              │
//   │   → 输出 [Q1·K2, Q1·K1, Q1·K0]                                  │
//   │                                                                 │
//   │ ═══════════════ 计算 Q2 与所有 K 的点积 ═══════════════          │
//   │                                                                 │
//   │ comp_prefill_q_cnt = 2, 读取 QCache[2] = Q2                     │
//   │   (重复上述过程...)                                              │
//   │   → 输出 [Q2·K2, Q2·K1, Q2·K0]                                  │
//   │   → compute_over = 1, 状态转换回 st_load                        │
//   │                                                                 │
//   └─────────────────────────────────────────────────────────────────┘

//   单个点积的计算细节

//   以计算 Q0·K0 为例，64 维向量分 2 批计算：

//   Q0 = [q0, q1, q2, ..., q31, q32, q33, ..., q63]
//         ├────── 前32维 ──────┤├────── 后32维 ──────┤

//   K0 = [k0, k1, k2, ..., k31, k32, k33, ..., k63]
//         ├────── 前32维 ──────┤├────── 后32维 ──────┤

//   第一批 (comp_headv_cnt=0)：
//   32个乘法器并行计算:
//     mul[0] = q0 × k0
//     mul[1] = q1 × k1
//     ...
//     mul[31] = q31 × k31

//   加法树求和:
//     部分和1 = mul[0] + mul[1] + ... + mul[31]
//             = q0×k0 + q1×k1 + ... + q31×k31

//   累加器:
//     acc_reg = 部分和1  (因为 acc_first=1，直接赋值)

//   第二批 (comp_headv_cnt=1)：
//   32个乘法器并行计算:
//     mul[0] = q32 × k32
//     mul[1] = q33 × k33
//     ...
//     mul[31] = q63 × k63

//   加法树求和:
//     部分和2 = q32×k32 + q33×k33 + ... + q63×k63

//   累加器:
//     acc_reg = acc_reg + 部分和2  (因为 acc_first=0，累加)
//             = 部分和1 + 部分和2
//             = Q0·K0  ← 完整的点积结果！

//   ---
//   四、Decode 模式完整流程

//   假设当前 seqlen = 2，即已有 K0, K1, K2 三个历史 K，现在生成新 token。

//   阶段1：收集新 token 的 Q 和 K

//   ┌─────────────────────────────────────────────────────────────────┐
//   │                    Load 阶段（收集数据）                          │
//   ├─────────────────────────────────────────────────────────────────┤
//   │                                                                 │
//   │  周期 0-31:   收集新 Token 的 Q_new 和 K_new                     │
//   │              ↓                                                  │
//   │  周期 32:    QKVec_valid=1                                      │
//   │              写入 QCache[0] = Q_new  ← 总是写地址0！             │
//   │              写入 KCache[2] = K_new  ← 追加到seqlen位置          │
//   │              状态转换: st_load → st_compute                      │
//   │                                                                 │
//   └─────────────────────────────────────────────────────────────────┘

//   关键区别：
//   - QCache 总是写地址 0（因为 Decode 只有 1 个新 Q）
//   - KCache 写地址 = lbatch_cnt × 26 + seqlen（追加到历史末尾）

//   Load 阶段结束后 Cache 状态：

//   QCache:
//   ┌─────────┬─────────────────────────────────┐
//   │ 地址    │ 内容                             │
//   ├─────────┼─────────────────────────────────┤
//   │   0     │ Q_new (新的Q，覆盖之前的)         │
//   │  1-7    │ (不关心)                         │
//   └─────────┴─────────────────────────────────┘

//   KCache:
//   ┌─────────┬─────────────────────────────────┐
//   │ 地址    │ 内容                             │
//   ├─────────┼─────────────────────────────────┤
//   │   0     │ K0 (历史)                        │
//   │   1     │ K1 (历史)                        │
//   │   2     │ K2 (历史，之前prefill写入的)      │
//   │   3     │ K_new (新追加的！)               │  ← seqlen+1 的位置
//   │  4-25   │ (未使用)                         │
//   └─────────┴─────────────────────────────────┘

//   阶段2：计算新 Q 与所有历史 K 的点积

//   需要计算的点积:
//   Q_new · K0
//   Q_new · K1
//   Q_new · K2
//   Q_new · K_new  (自注意力，新token也要和自己算)

//   注意：Decode 模式下 seqlen 应该更新为 3（包含新 token），所以要计算 4 个点积。

//   ┌─────────────────────────────────────────────────────────────────┐
//   │                  Compute 阶段（计算点积）                         │
//   ├─────────────────────────────────────────────────────────────────┤
//   │                                                                 │
//   │ comp_prefill_q_cnt 不递增（因为 is_prefill=0）                   │
//   │ 只读取 QCache[0] = Q_new                                        │
//   │                                                                 │
//   │   comp_key_cnt=0, 读取 KCache[0] = K0                           │
//   │     → 计算 Q_new·K0, 存入 res_cache[0]                          │
//   │                                                                 │
//   │   comp_key_cnt=1, 读取 KCache[1] = K1                           │
//   │     → 计算 Q_new·K1, 存入 res_cache[1]                          │
//   │                                                                 │
//   │   comp_key_cnt=2, 读取 KCache[2] = K2                           │
//   │     → 计算 Q_new·K2, 存入 res_cache[2]                          │
//   │                                                                 │
//   │   comp_key_cnt=3, 读取 KCache[3] = K_new                        │
//   │     → 计算 Q_new·K_new, 存入 res_cache[3]                       │
//   │     → res_valid = 1                                             │
//   │     → 输出 [Q_new·K_new, Q_new·K2, Q_new·K1, Q_new·K0]          │
//   │     → compute_over = 1                                          │
//   │                                                                 │
//   └─────────────────────────────────────────────────────────────────┘

//   ---
//   五、两种模式的关键区别总结
//   ┌──────────────────┬──────────────────────┬─────────────────────┐
//   │       方面       │     Prefill 模式     │     Decode 模式     │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ 输入             │ 多个 token 的 Q,K    │ 1 个新 token 的 Q,K │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ QCache 写地址    │ 0, 1, 2, ..., seqlen │ 总是 0              │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ KCache 写地址    │ 0, 1, 2, ..., seqlen │ seqlen（追加）      │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ 何时进入 Compute │ 所有 token 收集完    │ 立即                │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ Q 遍历次数       │ seqlen+1 次          │ 1 次                │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ K 遍历次数       │ seqlen+1 次          │ seqlen+1 次         │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ 输出次数         │ seqlen+1 次          │ 1 次                │
//   ├──────────────────┼──────────────────────┼─────────────────────┤
//   │ 输出内容         │ 每个 Q 对应一行点积  │ 新 Q 对应的一行点积 │
//   └──────────────────┴──────────────────────┴─────────────────────┘
//   ---
//   六、流水线时序图

//   以 Decode 模式，seqlen=2（计算 Q_new 与 K0,K1,K2 的点积）为例：

//   周期   状态    comp_headv  comp_key  操作
//   ─────────────────────────────────────────────────────────────────
//    0    compute     0          0      读 QCache[0], KCache[0]
//    1    compute     1          0      读 QCache[0], KCache[0] (同一对Q,K的第二批)
//    2    compute     0          1      读 QCache[0], KCache[1]
//    3    compute     1          1      读 QCache[0], KCache[1]
//    4    compute     0          2      读 QCache[0], KCache[2]
//    5    compute     1          2      读 QCache[0], KCache[2]
//                                       comp_key_last=1, compute_over=1

//    ... (流水线延迟，约8-9周期)

//   13                                  res_cache[0] = Q·K0
//   14                                  res_cache[1] = Q·K1
//   15                                  res_cache[2] = Q·K2, res_valid=1

//   ---
//   七、数据流图解

//                           ┌─────────────────────────────────────┐
//                           │            DM 模块                   │
//                           │                                     │
//     data_in ─────────────►│  ┌─────────┐      ┌─────────┐       │
//     (Q,K 元素)             │  │  QVec   │      │  KVec   │       │
//                           │  │ 拼接器  │      │ 拼接器  │       │
//                           │  └────┬────┘      └────┬────┘       │
//                           │       │                │            │
//                           │       ▼                ▼            │
//                           │  ┌─────────┐      ┌─────────┐       │
//                           │  │ QCache  │      │ KCache  │       │
//                           │  │ 深度8   │      │深度3328 │       │
//                           │  └────┬────┘      └────┬────┘       │
//                           │       │                │            │
//                           │       ▼                ▼            │
//                           │  ┌─────────┐      ┌─────────┐       │
//                           │  │ Q_Sel   │      │ K_Sel   │       │
//                           │  │ 选择32维│      │ 选择32维│       │
//                           │  └────┬────┘      └────┬────┘       │
//                           │       │                │            │
//                           │       └───────┬────────┘            │
//                           │               ▼                     │
//                           │       ┌───────────────┐             │
//                           │       │  32个乘法器    │             │
//                           │       │   mullist     │             │
//                           │       └───────┬───────┘             │
//                           │               ▼                     │
//                           │       ┌───────────────┐             │
//                           │       │   加法树       │             │
//                           │       │   addtree     │             │
//                           │       └───────┬───────┘             │
//                           │               ▼                     │
//                           │       ┌───────────────┐             │
//                           │       │   累加器       │             │
//                           │       │   acc_reg     │             │
//                           │       └───────┬───────┘             │
//                           │               ▼                     │
//                           │       ┌───────────────┐             │
//                           │       │  res_cache    │             │
//                           │       │  26个结果槽   │             │
//                           │       └───────┬───────┘             │
//                           │               │                     │
//                           └───────────────┼─────────────────────┘
//                                           ▼
//                                       data_out
//                                 (26个点积结果)

//   ---
//   八、常见疑问解答

//   Q1: 为什么 QCache 深度只有 8，而 KCache 深度有 3328？

//   - QCache: Prefill 最多 8 个 token，Decode 只需要 1 个 Q，所以深度 8 足够
//   - KCache: 需要保存所有历史 K，128 个 lbatch × 26 个 token = 3328

//   Q2: 为什么要分 2 批计算？

//   - 64 维向量，但只有 32 个乘法器
//   - 分 2 批：第一批算前 32 维，第二批算后 32 维，然后累加

//   Q3: comp_headv_cnt 和 comp_key_cnt 的关系？

//   comp_headv_cnt: 0 → 1 → 0 → 1 → 0 → 1 → ...  (每周期变化)
//   comp_key_cnt:   0 → 0 → 1 → 1 → 2 → 2 → ...  (每2周期变化)

//   内层循环（headv）完成一轮后，外层循环（key）才递增。

//   Q4: 为什么需要 PipReg 延迟控制信号？

//   因为数据经过 Cache读(1周期) → MuxLookup(1周期) → 乘法器(2周期) → 加法树(5周期) 共 9 周期延迟，控制信号也需要同样延迟才能对齐。
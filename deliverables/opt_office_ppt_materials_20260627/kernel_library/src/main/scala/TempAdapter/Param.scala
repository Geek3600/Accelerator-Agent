package TempAdapter

object Param {
  // LayerNorm 侧参数
  val LN_DATAW = 8              // LayerNorm 数据位宽
  val LN_SUBVEC = 12            // LayerNorm 每周期元素数
  val LN_VECTOR = 768           // LayerNorm 向量维度
  val LN_WIDTH = LN_DATAW * LN_SUBVEC  // = 96 bits
  val LN_DEPTH = 2048           // LayerNorm 内存深度

  // Attention 侧参数
  val LOAD_DATAW = 8            // Load0 数据位宽
  val LOAD_VECNUM = 2           // Load0 每周期元素数
  val HEAD_DIM = 64             // 注意力头维度
  val OUT_WIDTH = LOAD_DATAW * LOAD_VECNUM * 3  // = 48 bits [V1,V0|K1,K0|Q1,Q0]

  // 提取维度
  val EXTRACT_DIM = HEAD_DIM * 3  // = 192 (Q+K+V)

  // 通用参数
  val BATCHSIZE = 16
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN

  // 收集次数
  val COLLECT_NUM = LN_VECTOR / LN_SUBVEC  // = 768 / 12 = 64
  val OUTPUT_NUM = HEAD_DIM / LOAD_VECNUM   // = 64 / 2 = 32
}

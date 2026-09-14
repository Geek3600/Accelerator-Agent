package FFNUp

object Param {
  val DATAW = 8
  val BATCHSIZE = 16

  // Prefill/Decode 模式参数
  val MAX_SEQLEN = 16   // 最大序列长度
  val MAX_PREFILL = MAX_SEQLEN   // Prefill 模式最大 token 数

  // 计算阵列参数
  val ROW = 12          // 每周期处理 12 个输入元素
  val COL = 36          // 每周期输出 36 个元素

  // 权重矩阵尺寸: 768 × 3072 (H → 4H)
  val ROW_W = 768       // 输入维度
  val COL_W = 3072      // 输出维度 (4 * 768)

  // 分块参数
  val ROWBLOCK = ROW_W / ROW        // = 768/12 = 64
  val COLBLOCK = (COL_W + COL - 1) / COL  // = (3072+35)/36 = 86

  // 存储器参数
  val MEM_WIDTH = DATAW * ROW       // = 96 bits (12 个 8-bit 元素)
  val MEM_DEPTH = 2048              // 足够存储 Prefill 和 Decode 数据

  // 权重存储器参数
  val WMEM_WIDTH = DATAW * COL      // = 288 bits (36 个 8-bit 元素)
  val WMEM_DEPTH = ROW * ROWBLOCK * COLBLOCK  // = 12 * 64 * 86 = 66048
}

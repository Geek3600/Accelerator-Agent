package FFNDown

object Param {
  val DATAW = 8
  val BATCHSIZE = 16

  // Prefill/Decode 模式参数
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN

  // 计算阵列参数
  val ROW = 12          // 每周期处理 12 个输入元素
  val COL = 36          // 每周期输出 36 个元素

  // 权重矩阵尺寸: 3072 × 768 (4H → H)
  val ROW_W = 3072      // 输入维度 (4H)
  val COL_W = 768       // 输出维度 (H)

  // 分块参数
  val ROWBLOCK = ROW_W / ROW        // = 3072/12 = 256
  val COLBLOCK = (COL_W + COL - 1) / COL  // = (768+35)/36 = 22

  // 存储器参数
  val MEM_WIDTH = DATAW * ROW       // = 96 bits
  val MEM_DEPTH = 2048

  // 权重存储器参数
  val WMEM_WIDTH = DATAW * COL      // = 288 bits
  val WMEM_DEPTH = ROW * ROWBLOCK * COLBLOCK  // = 12 * 256 * 22 = 67584
}

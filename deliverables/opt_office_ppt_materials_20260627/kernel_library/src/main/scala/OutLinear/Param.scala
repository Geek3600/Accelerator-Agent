package OutLinear

object Param {
  val DATAW = 8
  val BATCHSIZE = 16

  // Prefill/Decode 模式参数
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN

  // 计算阵列参数
  val ROW = 12          // 每周期处理12个输入元素
  val COL = 36          // 36个输出通道

  // 矩阵维度: 768 x 768
  // 输入: 12 个 head 拼接后的 768 维向量
  // 输出: 768 维向量
  val ROW_W = 768
  val COL_W = 768       // 输出维度

  val ROWBLOCK = (ROW_W + ROW - 1) / ROW  // = 64
  val COLBLOCK = (COL_W + COL - 1) / COL  // = 22

  // 数据存储参数
  val MEM_WIDTH = DATAW * ROW          // = 96 bits (12个8-bit元素)
  val MEM_DEPTH = 2048

  // 每个注意力头的输出参数
  val HEAD_NUM = 12
  val HEAD_DIM = 64
  val HEAD_WIDTH = DATAW * HEAD_DIM    // = 512 bits

  // 权重存储参数
  val WMEM_WIDTH = DATAW * COL         // = 288 bits (36个8-bit元素)
  val WMEM_DEPTH = ROW * ROWBLOCK * COLBLOCK  // = 12 * 64 * 22 = 16896

  // 输出参数
  val OUT_VECTOR = COL_W               // = 768
  val SUBVEC = 12                      // 每周期输出元素数
}

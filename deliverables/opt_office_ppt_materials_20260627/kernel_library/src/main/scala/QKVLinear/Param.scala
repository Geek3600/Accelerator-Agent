package QKVLinear

object Param {
  val DATAW = 8
  val BATCHSIZE = 16

  // Prefill/Decode 模式参数
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN

  // 计算阵列参数
  val ROW = 12          // 每周期处理12个输入元素
  val COL = 36          // 36个输出通道

  // 矩阵维度: 768 x (768*3) = 768 x 2304
  // 输入: 768维向量
  // 输出: 2304维向量 (Q:768 + K:768 + V:768)
  val ROW_W = 768       // 输入维度
  val COL_W = 768 * 3   // 输出维度 = 2304 (Q/K/V 各768)

  val ROWBLOCK = ROW_W / ROW           // = 64 (输入分块数)
  val COLBLOCK = (COL_W + COL - 1) / COL  // = 64 (输出分块数)

  // 数据存储参数
  val MEM_WIDTH = DATAW * ROW          // = 96 bits (12个8-bit元素)
  val MEM_DEPTH = 2048

  // 权重存储参数
  val WMEM_WIDTH = DATAW * COL         // = 288 bits (36个8-bit元素)
  val WMEM_DEPTH = ROW * ROWBLOCK * COLBLOCK  // = 12 * 64 * 64 = 49152

  // 输出参数
  val OUT_VECTOR = COL_W               // = 2304 (Q/K/V 各768)
  val HEAD_DIM = 64                    // 每个头的维度
  val HEAD_NUM = 12                    // 注意力头数
}

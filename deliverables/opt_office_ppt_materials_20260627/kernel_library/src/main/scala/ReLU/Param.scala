package ReLU

object Param {
  val DATAW = 8
  val BATCHSIZE = 16

  // Prefill/Decode 模式参数
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN

  // 向量单元数（每周期处理的元素数）
  val VECNUM = 12

  // 数据维度：4H = 3072
  val DATA_DIM = 3072

  // 存储器参数
  val MEM_WIDTH = DATAW * VECNUM
  val MEM_DEPTH = 2048
}

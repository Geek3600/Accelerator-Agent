package ResAdd

object Param {
  // 数据格式参数
  val DATAW = 8                 // 数据位宽
  val SUBVEC = 12               // 每周期元素数
  val VECTOR = 768              // 向量维度
  val DATA_WIDTH = DATAW * SUBVEC  // = 96 bits

  // DM2 输出参数
  val DM2_VECNUM = 64           // DM2 输出向量维度
  val DM2_WIDTH = DATAW * DM2_VECNUM  // = 512 bits

  // 通用参数
  val BATCHSIZE = 16
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN

  // 收集/输出次数
  val COLLECT_NUM = VECTOR / SUBVEC  // = 768 / 12 = 64 (收集原始输入)
  val DM2_TO_OUT_NUM = DM2_VECNUM / SUBVEC  // = 64 / 12 ≈ 6 (DM2输出转换)

  // 内存深度
  val MEM_DEPTH = BATCHSIZE * COLLECT_NUM  // 缓存深度
}

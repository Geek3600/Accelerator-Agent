package DM2

object Param {
  val SINGLE_QUERY_BATCH = 12
  val BATCHSIZE = SINGLE_QUERY_BATCH // 当前 short-seq 只保留 12-head single-query 路径
  val LBANCHNUM = 4
  val LBATCHSIZE = BATCHSIZE * LBANCHNUM
  val HEAD_VECNUM = 64 // 每个注意力头的维度
  // 真实输入已收敛到 16-token 短序列，DM2 不再保留 912/26 的历史长度兼容壳子。
  val MAX_SEQLEN = 16
  val MAX_PREFILL = 16
  val TILE_SEQLEN = 16
  val MULNUM = 32 //乘法器数量
  val DATAW = 8 // 数据位宽
  val MEM_DEPTH = BATCHSIZE
}



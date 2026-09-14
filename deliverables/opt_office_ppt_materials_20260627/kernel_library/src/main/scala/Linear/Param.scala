package Linear


object Param {
  val DATAW = 8
  val BATCHSIZE = 32

  // Prefill/Decode 模式参数
  val MAX_SEQLEN = 16   // 最大序列长度
  val MAX_PREFILL = MAX_SEQLEN   // Prefill 模式最大 token 数

  val ROW = 12
  val COL = 36

  val ROW_W = 768
  val COL_W = 768

  val ROWBLOCK= ROW_W/ROW
  val COLBLOCK= (COL_W + COL - 1)/COL


  val MEM_WIDTH = DATAW * ROW
  val MEM_DEPTH = 2048

  val WMEM_WIDTH = DATAW * COL
  val WMEM_DEPTH = ROW * ROWBLOCK * COLBLOCK

  val COL_D = 768

  val V = 12

}

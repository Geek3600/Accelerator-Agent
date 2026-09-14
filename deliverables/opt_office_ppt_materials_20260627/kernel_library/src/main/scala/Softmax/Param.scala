package Softmax

object Param {
  val DATAW = 8
  val SINGLE_QUERY_BATCH = 12
  val BATCHSIZE = SINGLE_QUERY_BATCH
  val TILE_SEQLEN = 16
  val SEQ_LEN = 16
  val V = 16

  val MEM_WIDTH = DATAW * V
  val MEM_DEPTH = 2048

  val WMEM_WIDTH = 1 * V
  val WMEM_DEPTH = 2048
}

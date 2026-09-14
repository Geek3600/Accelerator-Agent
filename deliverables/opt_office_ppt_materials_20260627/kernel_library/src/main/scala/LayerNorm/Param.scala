package LayerNorm

object Param {

  val DATAW = 8
  val VECTOR = 768
  val SUBVECTOR = 12 // 假设 8
  val MEM_WIDTH = DATAW * SUBVECTOR // 示例
  val MEM_DEPTH = 2048
  val BATCHSIZE = 16
}

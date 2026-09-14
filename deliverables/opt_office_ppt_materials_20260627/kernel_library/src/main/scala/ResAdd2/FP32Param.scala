package ResAdd2

import QuantCommon.Precision._

object FP32Param {
  val DATAW = FP32_WIDTH
  val SUBVEC = LANES
  val DATA_WIDTH = FP32_PACK_WIDTH

  val BATCHSIZE = 16
  val MAX_SEQLEN = 16
  val MAX_PREFILL = MAX_SEQLEN
  val MEM_DEPTH = 2048
}

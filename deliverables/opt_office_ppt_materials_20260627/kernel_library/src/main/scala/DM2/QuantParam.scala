package DM2

import QuantCommon.Precision._

object QuantParam {
  val CTX_FP32_WIDTH = Param.TILE_SEQLEN * FP32_WIDTH
  val CTX_UINT8_WIDTH = Param.TILE_SEQLEN * UINT8_WIDTH
}

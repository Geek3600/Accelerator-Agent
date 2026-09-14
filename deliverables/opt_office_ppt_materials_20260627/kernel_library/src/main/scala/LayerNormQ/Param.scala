package LayerNormQ

import QuantCommon.Precision._

object Param {
  val VECTOR = 768
  val LANE_NUM = LANES
  val VECTOR_BEATS = VECTOR / LANE_NUM

  val FP_WIDTH = FP32_WIDTH
  val INT_WIDTH = INT8_WIDTH

  val FP_PACK_WIDTH = FP32_PACK_WIDTH
  val INT_PACK_WIDTH = INT8_PACK_WIDTH

  val MEM_DEPTH = 2048
  val BATCHSIZE = 16
}

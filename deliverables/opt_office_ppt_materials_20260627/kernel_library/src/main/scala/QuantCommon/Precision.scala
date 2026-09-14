package QuantCommon

import hardfloat.consts

object Precision {
  // 基础精度定义
  val INT8_WIDTH = 8
  val UINT8_WIDTH = 8
  val INT32_WIDTH = 32
  val FP32_WIDTH = 32

  // IEEE FP32 = 1(sign) + 8(exp) + 23(frac)
  // HardFloat 中 sigWidth 包含隐藏位，因此取 24
  val FP32_EXP_WIDTH = 8
  val FP32_SIG_WIDTH = 24

  // 当前加速器每拍处理 12 个元素
  val LANES = 12
  val SOFTMAX_LEN = 26

  // 常用打包位宽
  val INT8_PACK_WIDTH = INT8_WIDTH * LANES
  val FP32_PACK_WIDTH = FP32_WIDTH * LANES
  val SOFTMAX_FP32_PACK_WIDTH = FP32_WIDTH * SOFTMAX_LEN

  // 量化约束
  val SCALE_WIDTH = FP32_WIDTH
  val ZERO_POINT_WIDTH = UINT8_WIDTH

  // HardFloat 默认控制参数
  val ROUNDING_MODE = consts.round_near_even
  val DETECT_TININESS = consts.tininess_afterRounding
}

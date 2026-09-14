package QuantCommon

import QuantCommon.Precision._
import chisel3._
import chisel3.util._

object Pack {
  def asInt8Vec(data: UInt): Vec[UInt] = data.asTypeOf(Vec(LANES, UInt(INT8_WIDTH.W)))

  def asUInt8Vec(data: UInt): Vec[UInt] = data.asTypeOf(Vec(LANES, UInt(UINT8_WIDTH.W)))

  def asFp32Vec(data: UInt): Vec[UInt] = data.asTypeOf(Vec(LANES, UInt(FP32_WIDTH.W)))

  def packUInt8Vec(data: Seq[UInt]): UInt = Cat(data.reverse)

  def packInt8Vec(data: Seq[UInt]): UInt = Cat(data.reverse)

  def packFp32Vec(data: Seq[UInt]): UInt = Cat(data.reverse)
}

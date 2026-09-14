package QuantCommon

import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class QuantizeSmokeTop extends Module {
  val io = IO(new Bundle() {
    val int8_in = Input(UInt(INT8_PACK_WIDTH.W))
    val uint8_in = Input(UInt(INT8_PACK_WIDTH.W))
    val fp32_in = Input(UInt(FP32_PACK_WIDTH.W))
    val scale = Input(UInt(FP32_WIDTH.W))
    val invScale = Input(UInt(FP32_WIDTH.W))
    val uint8ZeroPoint = Input(UInt(UINT8_WIDTH.W))

    val int8_to_fp32 = Output(UInt(FP32_PACK_WIDTH.W))
    val uint8_to_fp32 = Output(UInt(FP32_PACK_WIDTH.W))
    val fp32_to_uint8 = Output(UInt(INT8_PACK_WIDTH.W))
  })

  val int8Dequant = Module(new Int8DequantizePack)
  int8Dequant.io.in := io.int8_in
  int8Dequant.io.scale := io.scale

  val uint8Dequant = Module(new UInt8DequantizePack)
  uint8Dequant.io.in := io.uint8_in
  uint8Dequant.io.zeroPoint := io.uint8ZeroPoint
  uint8Dequant.io.scale := io.scale

  val fp32Quant = Module(new Fp32QuantizeToUInt8Pack)
  fp32Quant.io.in := io.fp32_in
  fp32Quant.io.invScale := io.invScale
  fp32Quant.io.zeroPoint := io.uint8ZeroPoint

  io.int8_to_fp32 := int8Dequant.io.out
  io.uint8_to_fp32 := uint8Dequant.io.out
  io.fp32_to_uint8 := fp32Quant.io.out
}

class QuantizeSpec extends AnyFreeSpec with Matchers {
  private val fp32One = "h3f800000".U(FP32_WIDTH.W)

  "Quantize modules should map zero paths correctly" in {
    simulate(new QuantizeSmokeTop) { dut =>
      dut.io.int8_in.poke(0.U(INT8_PACK_WIDTH.W))
      dut.io.uint8_in.poke(0.U(INT8_PACK_WIDTH.W))
      dut.io.fp32_in.poke(0.U(FP32_PACK_WIDTH.W))
      dut.io.scale.poke(fp32One)
      dut.io.invScale.poke(fp32One)
      dut.io.uint8ZeroPoint.poke(0.U)
      dut.clock.step()

      dut.io.int8_to_fp32.peek().litValue mustBe 0
      dut.io.uint8_to_fp32.peek().litValue mustBe 0
      dut.io.fp32_to_uint8.peek().litValue mustBe 0
    }
  }
}

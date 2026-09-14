package Softmax

import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class SoftmaxFP32Spec extends AnyFreeSpec with Matchers {
  private def fp32Bits(value: Float): BigInt =
    BigInt(java.lang.Integer.toUnsignedLong(java.lang.Float.floatToRawIntBits(value)))

  "SoftmaxFP32 should keep 26-lane behavior and map a single valid zero logit to 1.0" in {
    simulate(new SoftmaxFP32) { dut =>
      for (i <- 0 until FP32Param.V) {
        dut.io.in(i).poke(fp32Bits(0.0f).U(FP32_WIDTH.W))
        dut.io.in_mask(i).poke((i == 0).B)
      }

      dut.clock.step()

      dut.io.out(0).peek().litValue mustBe fp32Bits(1.0f)
      for (i <- 1 until FP32Param.V) {
        dut.io.out(i).peek().litValue mustBe 0
      }
    }
  }
}

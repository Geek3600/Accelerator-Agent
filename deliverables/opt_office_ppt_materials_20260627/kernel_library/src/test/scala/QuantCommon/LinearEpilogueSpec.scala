package QuantCommon

import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class LinearEpilogueSpec extends AnyFreeSpec with Matchers {
  "Int32AccToFp32Pack should map zero accumulators to zero with zero bias" in {
    simulate(new Int32AccToFp32Pack) { dut =>
      dut.io.in.poke(0.U(FP32_PACK_WIDTH.W))
      dut.io.scale.poke("h3f800000".U(FP32_WIDTH.W))
      dut.io.bias.poke(0.U(FP32_PACK_WIDTH.W))
      dut.clock.step()
      dut.io.out.peek().litValue mustBe 0
    }
  }
}

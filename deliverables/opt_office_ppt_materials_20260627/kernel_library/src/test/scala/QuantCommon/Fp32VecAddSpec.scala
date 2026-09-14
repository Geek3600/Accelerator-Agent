package QuantCommon

import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class Fp32VecAddSpec extends AnyFreeSpec with Matchers {
  "Fp32VecAdd should elaborate and process zero vectors" in {
    simulate(new Fp32VecAdd) { dut =>
      dut.io.a.poke(0.U(FP32_PACK_WIDTH.W))
      dut.io.b.poke(0.U(FP32_PACK_WIDTH.W))
      dut.clock.step()

      dut.io.out.peek().litValue mustBe 0
      dut.io.exceptionFlags.foreach(_.peek().litValue mustBe 0)
    }
  }
}

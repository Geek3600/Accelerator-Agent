package Softmax

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class EXP2Spec extends AnyFreeSpec with Matchers {
  "Exp2 should expand fixed-point inputs" in {
    simulate(new Exp2(2, 8, 8)) { dut =>
      dut.io.in(0).poke(0.S)
      dut.io.in(1).poke((1 << 8).S)
      dut.clock.step()

      dut.io.out(0).peek().litValue mustBe BigInt(1 << 8)
      dut.io.out(1).peek().litValue mustBe BigInt(2 << 8)
    }
  }
}

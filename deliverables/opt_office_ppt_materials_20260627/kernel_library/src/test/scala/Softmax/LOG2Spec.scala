package Softmax

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class Log2Spec extends AnyFreeSpec with Matchers {
  "Log2 should return zero for fixed-point one" in {
    simulate(new Log2(1)) { dut =>
      dut.io.in(0).poke((1 << 8).S)
      dut.clock.step()

      dut.io.out(0).peek().litValue mustBe BigInt(0)
    }
  }
}

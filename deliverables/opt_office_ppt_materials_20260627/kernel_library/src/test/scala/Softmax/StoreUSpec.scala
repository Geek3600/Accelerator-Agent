package Softmax

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class StoreUSpec extends AnyFreeSpec with Matchers {
  "StoreUnit should forward one valid beat" in {
    simulate(new StoreUnit) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_seqlen.poke(1.U)
      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_valid.poke(true.B)
      dut.io.data_in.poke(0x55.U)
      dut.io.data_in_valid.poke(true.B)
      dut.clock.step()

      dut.io.cfg_valid.poke(false.B)
      dut.io.data_out_valid.peek().litToBoolean mustBe true

      dut.io.data_in_valid.poke(false.B)
      dut.clock.step()
    }
  }
}

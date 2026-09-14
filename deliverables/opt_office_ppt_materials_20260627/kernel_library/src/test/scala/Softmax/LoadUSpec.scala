package Softmax

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class LoadUSpec extends AnyFreeSpec with Matchers {
  "LoadUnit should raise valid after starting a prefill transfer" in {
    simulate(new LoadUnit) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_valid.poke(true.B)
      dut.io.data_in.poke(0x1234.U)
      dut.io.data_in_ready.poke(true.B)
      dut.io.data_out_ready.poke(true.B)
      dut.clock.step()
      dut.io.cfg_valid.poke(false.B)

      dut.clock.step()

      dut.io.data_out_valid.peek().litToBoolean mustBe true
    }
  }
}

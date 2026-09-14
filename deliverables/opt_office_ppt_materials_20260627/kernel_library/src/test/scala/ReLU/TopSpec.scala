package ReLU

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class TopSpec extends AnyFreeSpec with Matchers {
  "ReLU top should preserve output address ordering" in {
    simulate(new ReLU) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_valid.poke(true.B)
      dut.io.data_out_ready.poke(true.B)
      dut.io.data_in_st.poke(true.B)
      dut.io.data_in.poke(0.U)
      dut.io.data_in_addr.poke(0.U)
      dut.io.data_in_valid.poke(true.B)
      dut.io.data_in_last.poke(true.B)
      dut.clock.step()

      dut.io.cfg_valid.poke(false.B)
      dut.io.data_in_st.poke(false.B)
      dut.io.data_in_valid.poke(false.B)
      dut.io.data_in_last.poke(false.B)

      var sawZeroAddr = false
      for (_ <- 0 until 40) {
        if (dut.io.data_out_valid.peek().litToBoolean && dut.io.data_out_addr.peek().litValue == 0) {
          sawZeroAddr = true
        }
        dut.clock.step()
      }

      sawZeroAddr mustBe true
    }
  }
}

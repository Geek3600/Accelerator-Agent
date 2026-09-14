package Softmax

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class SoftmaxSpec extends AnyFreeSpec with Matchers {
  "SoftmaxPip should produce output with a zero mask" in {
    simulate(new SoftmaxPip) { dut =>
      val inputData = (1 to 26).map(i => BigInt(i) << ((i - 1) * 8)).sum

      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_valid.poke(true.B)
      dut.io.layer_st.poke(true.B)
      dut.io.data_in_st.poke(true.B)
      dut.io.data_in.poke(inputData.U)
      dut.io.data_addr.poke(0.U)
      dut.io.data_valid.poke(true.B)
      dut.io.data_last.poke(true.B)
      dut.io.w_in.poke(0.U)
      dut.io.res_ready.poke(true.B)
      dut.clock.step()

      dut.io.cfg_valid.poke(false.B)
      dut.io.layer_st.poke(false.B)
      dut.io.data_in_st.poke(false.B)
      dut.io.data_valid.poke(false.B)
      dut.io.data_last.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 80) {
        if (dut.io.res_valid.peek().litToBoolean) {
          sawOutput = true
        }
        dut.clock.step()
      }

      sawOutput mustBe true
    }
  }
}

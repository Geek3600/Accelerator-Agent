package ResAdd2

import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class ResAdd2FP32Spec extends AnyFreeSpec with Matchers {
  "ResAdd2FP32 should add zero vectors" in {
    simulate(new ResAdd2FP32) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_valid.poke(false.B)
      dut.io.res_ready.poke(true.B)

      dut.io.s7_in.poke(0.U(FP32_PACK_WIDTH.W))
      dut.io.s7_in_st.poke(true.B)
      dut.io.s7_in_addr.poke(0.U)
      dut.io.s7_in_valid.poke(true.B)
      dut.io.s7_in_last.poke(true.B)
      dut.clock.step()

      dut.io.s7_in_st.poke(false.B)
      dut.io.s7_in_valid.poke(false.B)
      dut.io.s7_in_last.poke(false.B)

      dut.io.ffn_in.poke(0.U(FP32_PACK_WIDTH.W))
      dut.io.ffn_in_st.poke(true.B)
      dut.io.ffn_in_addr.poke(0.U)
      dut.io.ffn_in_valid.poke(true.B)
      dut.io.ffn_in_last.poke(true.B)
      dut.clock.step()

      dut.io.ffn_in_st.poke(false.B)
      dut.io.ffn_in_valid.poke(false.B)
      dut.io.ffn_in_last.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 20) {
        if (dut.io.res_valid.peek().litToBoolean) {
          sawOutput = true
          dut.io.res.peek().litValue mustBe 0
        }
        dut.clock.step()
      }

      sawOutput mustBe true
    }
  }
}

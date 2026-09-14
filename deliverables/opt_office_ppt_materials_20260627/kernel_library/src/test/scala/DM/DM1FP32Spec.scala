package DM

import DM.FP32Param._
import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class DM1FP32Spec extends AnyFreeSpec with Matchers {
  "DM1FP32 should produce zero logits for zero Q and K" in {
    simulate(new DM1FP32) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_valid.poke(true.B)
      dut.io.out_scale.poke("h3f800000".U(FP32_WIDTH.W))
      dut.io.res_ready.poke(true.B)
      dut.clock.step()
      dut.io.cfg_valid.poke(false.B)

      for (addr <- 0 until (HEAD_VECNUM / LOAD_VECNUM)) {
        dut.io.data_in_st.poke(addr == 0)
        dut.io.data_in.poke(0.U((2 * LOAD_VECNUM * DATAW).W))
        dut.io.data_addr.poke(addr.U)
        dut.io.data_valid.poke(true.B)
        dut.io.data_last.poke(addr == (HEAD_VECNUM / LOAD_VECNUM - 1))
        dut.clock.step()
      }
      dut.io.data_in_st.poke(false.B)
      dut.io.data_valid.poke(false.B)
      dut.io.data_last.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 2000) {
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

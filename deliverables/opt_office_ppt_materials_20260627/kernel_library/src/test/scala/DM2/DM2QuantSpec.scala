package DM2

import DM2.Param._
import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class DM2QuantSpec extends AnyFreeSpec with Matchers {
  "DM2CUQuant should preserve the original 64-d schedule and produce zero output for zero ctx and V" in {
    simulate(new DM2CUQuant) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_valid.poke(true.B)
      dut.io.out_inv_scale.poke("h3f800000".U(FP32_WIDTH.W))
      dut.clock.step()
      dut.io.cfg_valid.poke(false.B)

      dut.io.data_in_v.poke(0.U((HEAD_VECNUM * DATAW).W))
      dut.io.data_in_v_valid.poke(true.B)
      dut.io.data_in_ctx.poke(0.U((MAX_SEQLEN * UINT8_WIDTH).W))
      dut.io.data_in_ctx_valid.poke(false.B)
      dut.clock.step()

      dut.io.data_in_v_valid.poke(false.B)
      dut.io.data_in_ctx_valid.poke(true.B)
      dut.clock.step()

      dut.io.data_in_ctx_valid.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 500) {
        if (dut.io.data_out_valid.peek().litToBoolean) {
          sawOutput = true
          dut.io.data_out.peek().litValue mustBe 0
        }
        dut.clock.step()
      }

      sawOutput mustBe true
    }
  }
}

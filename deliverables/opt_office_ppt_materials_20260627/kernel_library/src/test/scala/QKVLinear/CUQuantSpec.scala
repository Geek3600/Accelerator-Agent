package QKVLinear

import QKVLinear.Param._
import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class CUQuantSpec extends AnyFreeSpec with Matchers {
  "CUQuant should keep zero accumulations at zero after requantization" in {
    simulate(new CUQuant) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_valid.poke(true.B)
      dut.io.out_inv_scale.poke("h3f800000".U(FP32_WIDTH.W))
      dut.clock.step()
      dut.io.cfg_valid.poke(false.B)

      dut.io.w_valid.poke(true.B)
      dut.io.w_data.poke(0.U(WMEM_WIDTH.W))
      for (_ <- 0 until ROW) {
        dut.clock.step()
      }
      dut.io.w_valid.poke(false.B)

      dut.io.data_in_valid.poke(true.B)
      dut.io.data_in.poke(0.U(MEM_WIDTH.W))
      for (_ <- 0 until ROWBLOCK) {
        dut.clock.step()
      }
      dut.io.data_in_valid.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 200) {
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

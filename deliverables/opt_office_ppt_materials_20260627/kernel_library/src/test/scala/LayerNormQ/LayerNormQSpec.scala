package LayerNormQ

import LayerNormQ.Param._
import QuantCommon.Precision._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class LayerNormQSpec extends AnyFreeSpec with Matchers {
  private def packFp32(words: Seq[BigInt]): BigInt =
    words.zipWithIndex.foldLeft(BigInt(0)) { case (acc, (word, idx)) =>
      acc | (word << (idx * FP32_WIDTH))
    }

  "LayerNormQ should map zero input to zero INT8 output when beta is zero" in {
    simulate(new LayerNormQ) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      // load beta = 0
      for (_ <- 0 until VECTOR_BEATS) {
        dut.io.w_in.poke(packFp32(Seq.fill(LANE_NUM)(BigInt(0))).U(FP_PACK_WIDTH.W))
        dut.io.w_valid.poke(true.B)
        dut.clock.step()
      }
      // load gamma = 1
      for (_ <- 0 until VECTOR_BEATS) {
        dut.io.w_in.poke(packFp32(Seq.fill(LANE_NUM)(BigInt("3f800000", 16))).U(FP_PACK_WIDTH.W))
        dut.io.w_valid.poke(true.B)
        dut.clock.step()
      }
      dut.io.w_valid.poke(false.B)

      dut.io.out_inv_scale.poke("h3f800000".U(FP32_WIDTH.W))
      dut.io.out_zero_point.poke(0.S)
      dut.io.res_ready.poke(true.B)

      for (addr <- 0 until VECTOR_BEATS) {
        dut.io.data_in_st.poke(addr == 0)
        dut.io.data_in.poke(packFp32(Seq.fill(LANE_NUM)(BigInt(0))).U(FP_PACK_WIDTH.W))
        dut.io.data_addr.poke(addr.U)
        dut.io.data_valid.poke(true.B)
        dut.io.data_last.poke(addr == VECTOR_BEATS - 1)
        dut.clock.step()
      }
      dut.io.data_valid.poke(false.B)
      dut.io.data_in_st.poke(false.B)
      dut.io.data_last.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 400) {
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

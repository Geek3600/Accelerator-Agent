package ReLU

import ReLU.Param._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class ReLUSpec extends AnyFreeSpec with Matchers {
  private def pack(data: Seq[Int]): BigInt = {
    data.zipWithIndex.foldLeft(BigInt(0)) { case (acc, (value, index)) =>
      acc | (BigInt(value & 0xFF) << (index * 8))
    }
  }

  "ReLU top should produce output after one full vector" in {
    simulate(new ReLU) { dut =>
      val chunk = pack(0 until 12)
      val beatsPerVector = DATA_DIM / VECNUM

      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.cfg_prefill.poke(true.B)
      dut.io.cfg_seqlen.poke(0.U)
      dut.io.cfg_valid.poke(true.B)
      dut.io.data_out_ready.poke(true.B)
      dut.io.data_in_st.poke(false.B)
      dut.io.data_in.poke(0.U)
      dut.io.data_in_addr.poke(0.U)
      dut.io.data_in_valid.poke(false.B)
      dut.io.data_in_last.poke(false.B)
      dut.clock.step()
      dut.io.cfg_valid.poke(false.B)

      for (addr <- 0 until beatsPerVector) {
        dut.io.data_in_st.poke(addr == 0)
        dut.io.data_in.poke(chunk.U)
        dut.io.data_in_addr.poke(addr.U)
        dut.io.data_in_valid.poke(true.B)
        dut.io.data_in_last.poke(addr == beatsPerVector - 1)
        dut.clock.step()
      }
      dut.io.data_in_valid.poke(false.B)
      dut.io.data_in_st.poke(false.B)
      dut.io.data_in_last.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 320) {
        if (dut.io.data_out_valid.peek().litToBoolean) {
          sawOutput = true
        }
        dut.clock.step()
      }

      sawOutput mustBe true
    }
  }
}

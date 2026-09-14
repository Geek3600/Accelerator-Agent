package LayerNorm

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec

class SimpleLayerNormTest extends AnyFreeSpec {
  private def pack(data: Seq[Int]): BigInt = {
    var packed = BigInt(0)
    for (i <- data.indices) {
      packed |= BigInt(data(i) & 0xFF) << (i * 8)
    }
    packed
  }

  "LayerNormCU should emit output after loading weights and one vector" in {
    simulate(new LayerNormCU) { dut =>
      val beatsPerVector = 768 / 12
      val alternating = Seq.fill(6)(Seq(2, 4)).flatten

      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.data_in.poke(0.U)
      dut.io.data_in_valid.poke(false.B)
      dut.io.w_data.poke(0.U)
      dut.io.w_valid.poke(false.B)

      dut.io.w_valid.poke(true.B)
      for (_ <- 0 until beatsPerVector) {
        dut.io.w_data.poke(0.U)
        dut.clock.step()
      }
      for (_ <- 0 until beatsPerVector) {
        dut.io.w_data.poke(pack(Seq.fill(12)(1)).U)
        dut.clock.step()
      }
      dut.io.w_valid.poke(false.B)

      dut.io.data_in_valid.poke(true.B)
      for (_ <- 0 until beatsPerVector) {
        dut.io.data_in.poke(pack(alternating).U)
        dut.clock.step()
      }
      dut.io.data_in_valid.poke(false.B)

      var sawOutput = false
      for (_ <- 0 until 200) {
        if (dut.io.data_out_valid.peek().litToBoolean) {
          sawOutput = true
        }
        dut.clock.step()
      }

      assert(sawOutput, "LayerNormCU never produced output")
    }
  }
}

import OutLinear.OutLinear
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class OutLinearConcatSpec extends AnyFreeSpec with Matchers {
  "OutLinear should wait for all heads and emit one 768-d token result" in {
    simulate(new OutLinear) { dut =>
      val headData = BigInt("0123456789abcdef", 16)

      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      dut.io.layer_st.poke(true.B)
      dut.io.weight_init_mode.poke(false.B)
      dut.io.weight_init_data.poke(0.U)
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

      dut.io.layer_st.poke(false.B)
      dut.io.cfg_valid.poke(false.B)

      for (head <- 0 until 11) {
        dut.io.data_in_st.poke(head == 0)
        dut.io.data_in.poke((headData + head).U)
        dut.io.data_in_addr.poke(0.U)
        dut.io.data_in_valid.poke(true.B)
        dut.io.data_in_last.poke(true.B)
        dut.clock.step()
      }

      dut.io.data_in_valid.poke(false.B)
      dut.io.data_in_st.poke(false.B)
      dut.io.data_in_last.poke(false.B)

      for (_ <- 0 until 40) {
        dut.io.data_out_valid.peek().litToBoolean mustBe false
        dut.clock.step()
      }

      dut.io.data_in.poke((headData + 11).U)
      dut.io.data_in_addr.poke(0.U)
      dut.io.data_in_valid.poke(true.B)
      dut.io.data_in_last.poke(true.B)
      dut.clock.step()
      dut.io.data_in_valid.poke(false.B)
      dut.io.data_in_last.poke(false.B)

      var outCount = 0
      var sawLast = false
      for (_ <- 0 until 2000) {
        if (dut.io.data_out_valid.peek().litToBoolean) {
          outCount += 1
          if (dut.io.data_out_last.peek().litToBoolean) {
            sawLast = true
          }
        }
        dut.clock.step()
      }

      sawLast mustBe true
      outCount mustBe 64
    }
  }
}

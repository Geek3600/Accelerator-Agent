package FFNUp

import FFNUp.Param._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class FusedPostProcessHarness extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val bias_in = Input(UInt(MEM_WIDTH.W))
    val data_out = Output(UInt(MEM_WIDTH.W))
  })

  val suVec = io.data_in.asTypeOf(Vec(ROW, SInt(DATAW.W)))
  val biasVec = io.bias_in.asTypeOf(Vec(ROW, SInt(DATAW.W)))
  val reluVec = Wire(Vec(ROW, UInt(DATAW.W)))

  for (i <- 0 until ROW) {
    val sum = suVec(i) +& biasVec(i)
    val maxVal = ((1 << (DATAW - 1)) - 1).S
    val minVal = (-(1 << (DATAW - 1))).S
    val sat = Mux(sum > maxVal, maxVal, Mux(sum < minVal, minVal, sum(DATAW - 1, 0).asSInt))
    reluVec(i) := Mux(sat < 0.S, 0.U, sat.asUInt)
  }

  io.data_out := reluVec.asUInt
}

class FusedPostProcessSpec extends AnyFreeSpec with Matchers {
  private def packBytes(values: Seq[Int]): BigInt =
    values.zipWithIndex.foldLeft(BigInt(0)) { case (acc, (value, idx)) =>
      acc | (BigInt(value & 0xff) << (idx * DATAW))
    }

  "FFNUp fused bias and ReLU logic should clamp negatives to zero" in {
    simulate(new FusedPostProcessHarness) { dut =>
      val expected = Seq(0, 2, 0, 4, 0, 6, 0, 8, 0, 10, 0, 12)
      val packedExpected = packBytes(expected)

      dut.io.data_in.poke(0.U(MEM_WIDTH.W))
      dut.io.bias_in.poke(packBytes(Seq(-1, 2, -3, 4, -5, 6, -7, 8, -9, 10, -11, 12)).U(MEM_WIDTH.W))
      dut.clock.step()

      dut.io.data_out.peek().litValue mustBe packedExpected
    }
  }
}

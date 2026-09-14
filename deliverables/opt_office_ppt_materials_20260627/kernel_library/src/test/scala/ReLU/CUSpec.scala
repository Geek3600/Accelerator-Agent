package ReLU

import ReLU._
import ReLU.Param._
import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class CUSpec extends AnyFreeSpec with Matchers {
  "CU should implement ReLU elementwise" in {
    simulate(new CU) { dut =>
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)

      val in = Seq(
        0x80, 0xFF, 0x00, 0x01, 0x7F, 0x81,
        0x02, 0xFE, 0x10, 0xF0, 0x20, 0xE0
      )

      val packedIn = in.zipWithIndex.foldLeft(BigInt(0)) { case (acc, (value, idx)) =>
        acc | (BigInt(value) << (idx * 8))
      }
      val expected = Seq(0, 0, 0, 1, 0x7F, 0, 2, 0, 0x10, 0, 0x20, 0)
      val packedExpected = expected.zipWithIndex.foldLeft(BigInt(0)) { case (acc, (value, idx)) =>
        acc | (BigInt(value) << (idx * 8))
      }

      dut.io.data_in.poke(packedIn.U(MEM_WIDTH.W))
      dut.io.data_in_valid.poke(true.B)
      dut.clock.step()

      dut.io.data_out_valid.peek().litToBoolean mustBe true
      dut.io.data_out.peek().litValue mustBe packedExpected

      dut.io.data_in_valid.poke(false.B)
      dut.clock.step()
    }
  }
}

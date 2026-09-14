package QuantCommon

import chisel3._
import chisel3.simulator.EphemeralSimulator._
import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.must.Matchers

class Fp32WrapperSpec extends AnyFreeSpec with Matchers {
  "basic FP32 wrappers should elaborate and process zero values" in {
    simulate(new Fp32Add) { dut =>
      dut.io.a.poke(0.U)
      dut.io.b.poke(0.U)
      dut.clock.step()
      dut.io.out.peek().litValue mustBe 0
    }

    simulate(new Int8ToFp32) { dut =>
      dut.io.in.poke(0.S)
      dut.clock.step()
      dut.io.out.peek().litValue mustBe 0
    }

    simulate(new Fp32ToUInt8) { dut =>
      dut.io.in.poke(0.U)
      dut.clock.step()
      dut.io.out.peek().litValue mustBe 0
    }
  }
}

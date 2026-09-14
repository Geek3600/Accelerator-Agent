import chisel3._
import circt.stage.ChiselStage
import org.scalatest.freespec.AnyFreeSpec

class SimpleTopTest extends AnyFreeSpec {
  "Top should elaborate successfully" in {
    val verilog = ChiselStage.emitSystemVerilog(new Top, firtoolOpts = Array("-disable-all-randomization"))
    assert(verilog.nonEmpty)
  }
}

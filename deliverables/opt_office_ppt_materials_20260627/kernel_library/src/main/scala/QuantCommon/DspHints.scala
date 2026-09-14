package QuantCommon

import chisel3.Data
import chisel3.experimental.{BaseModule, Targetable, annotate}
import firrtl.AttributeAnnotation
import firrtl.annotations.Named

object DspHints {
  private def emitUseDsp[T](target: T)(named: => Named)(implicit targetable: Targetable[T]): Unit = {
    annotate(Seq(target)) {
      Seq(AttributeAnnotation(named, "use_dsp = \"yes\""))
    }
  }

  def preferDsp(target: BaseModule): Unit = emitUseDsp(target)(target.toNamed)
  def preferDsp(target: Data): Unit = emitUseDsp(target)(target.toNamed)
}

package QuantCommon

object FpBackend {
  sealed trait Mode
  case object HardFloatCompat extends Mode
  case object VivadoIp extends Mode

  private var current: Mode = HardFloatCompat

  def mode: Mode = current
  def useVivadoIp: Boolean = current == VivadoIp

  def setHardFloatCompat(): Unit = {
    current = HardFloatCompat
  }

  def setVivadoIp(): Unit = {
    current = VivadoIp
  }
}

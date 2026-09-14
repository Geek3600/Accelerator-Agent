Use this directory to package a standalone Vivado IP that does not conflict with the original cnn_core IP.

Files:
  hdl/opt_acc_core.sv   - board-compatible wrapper with module name opt_acc_core
  hdl/Top_vivado.sv     - synthesis-oriented copy of generated Top with verification/assert fragments stripped

Recommended Vivado IP identity:
  Vendor  = user.org
  Library = user
  Name    = opt_acc_core
  Version = 1.0

Do not package this IP as cnn_core, otherwise the original cnn_core_1 instance in the sample BD may become locked.

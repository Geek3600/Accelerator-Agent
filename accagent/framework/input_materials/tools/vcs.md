# VCS工具位置和使用方式

* 所在机器：hyyuan@10.12.133.23
* 用途：功能验证阶段，用于编译和运行 SystemVerilog testbench。
* 可执行文件：/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs
* 版本探测命令：
  * `VCS_TARGET_ARCH=linux64 /home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs -ID`
* Stage 0 必须通过 SSH 实际探测该命令可调用，不能只因为文档里写了路径就认为 VCS 可用。
* 运行 VCS 时需要设置：
  * `VCS_TARGET_ARCH=linux64`
  * `REMOTE_HOST=hyyuan@10.12.133.23`
  * `REMOTE_VCS_HOME=/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109`
* 当前框架已有的 Qwen VCS smoke 脚本：
  * `scripts/verification/run_qwen_generated_vcs_smoke_23.sh`
* VCS 主要用于真实功能验证；如果后续用户改用 Verilator，Stage 0 也必须从工具材料中提取 Verilator 的位置和限制。

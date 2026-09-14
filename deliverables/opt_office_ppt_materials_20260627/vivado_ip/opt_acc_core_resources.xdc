# ============================================================
# opt_acc_core 资源约束
# 适用场景：已将 opt_acc_core 接入 v0825 的 Block Design 后，
#          在顶层工程中作为额外 XDC 加入综合/实现。
#
# 目标：
#   1. 强制关键乘法器走 DSP48E2
#   2. 强制大容量权重/Attention 中间缓存走 URAM
#   3. 强制中小容量缓存走 BRAM，避免 LUTRAM 爆炸
#
# 注意：
#   - 这里不再添加 create_clock，BD 顶层已有时钟约束。
#   - 这里不使用旧 cnn_core 的层次路径，而是按当前 opt_acc_core
#     内部综合后唯一的 REF_NAME 做约束，避免实例名变化导致失效。
# ============================================================

# ------------------------------------------------------------
# 0. 高扇出控制信号
# ------------------------------------------------------------
# 这部分改为 RTL 属性实现，避免 XDC 在综合前命中不到内部 net 时
# 产生 `Common 17-55` 类 critical warning。

# ------------------------------------------------------------
# 1. DSP 约束
# ------------------------------------------------------------
# 线性层 / FFN / QKV 的 8x8 乘法器
set_property USE_DSP yes [get_cells -quiet -hier -filter {
    REF_NAME =~ "SignedMultiplierInt8*" ||
    REF_NAME =~ "UnsignedSignedMultiplierInt8*" ||
    REF_NAME =~ "SignedMacChain32*"
}]

# 新的 MAC 串联链也要显式打上 DSP 提示；否则替换掉旧 addTree 之后，
# 原先只命中 SignedAddTree32 / mul_list 的约束会整体失效。
set_property USE_DSP yes [get_cells -quiet -hier -filter {REF_NAME =~ "SignedMacChain32*"}]

# 兼容旧层次名的兜底匹配，避免某些综合版本只保留实例名
set_property USE_DSP yes [get_cells -quiet -hier -filter {
    NAME =~ "*mul_list_*" ||
    NAME =~ "*macChainList_*" ||
    NAME =~ "*SignedMacChain32*" ||
    NAME =~ "*SignedMultiplierInt8*" ||
    NAME =~ "*UnsignedSignedMultiplierInt8*"
}]

# ------------------------------------------------------------
# 2. URAM 约束
# ------------------------------------------------------------
# 2.1 大矩阵权重存储
# 当前四个大线性模块的 WeightMem 已改成显式 XPM URAM wrapper，
# 不再依赖 inferred RAM + RAM_STYLE 约束推断。

# 2.2 DM / DM2 里的大容量 512-bit 缓存
# 现已改成显式 XPM URAM wrapper，不再依赖 inferred RAM + RAM_STYLE。

# ------------------------------------------------------------
# 3. BRAM 约束
# ------------------------------------------------------------
# 3.1 线性层/FFN/Out/QKV 的双缓冲 DataMem
set_property RAM_STYLE BLOCK [get_cells -quiet -hier -filter {REF_NAME == mem_2048x96}]

# 3.2 DM1 score/int32 中间缓存
set_property RAM_STYLE BLOCK [get_cells -quiet -hier -filter {REF_NAME == mem_2048x32}]

# 3.3 ResMEM / VCache 小块缓冲
set_property RAM_STYLE BLOCK [get_cells -quiet -hier -filter {REF_NAME == mem_832x16}]

# 3.4 中等容量缓存
# ResAdd / ResAdd2 当前使用 2048x384 双缓冲
set_property RAM_STYLE BLOCK [get_cells -quiet -hier -filter {REF_NAME == mem_2048x384}]

# mem_26x512：DM 当前小深度宽缓存，避免落 LUTRAM
set_property RAM_STYLE BLOCK [get_cells -quiet -hier -filter {REF_NAME == mem_26x512}]

# ------------------------------------------------------------
# 4. 说明
# ------------------------------------------------------------
# 当前这份约束是按 Top_vivado.sv 实际综合出来的 REF_NAME 写的：
#   - DSP: SignedMultiplierInt8 / SignedMultiplierInt8_432 / UnsignedSignedMultiplierInt8 / SignedMacChain32
#   - URAM: weight_banks_4096x72 / mem_10944x512
#   - BRAM: mem_2048x96 / mem_2048x32 / mem_832x16 / mem_2048x384 / mem_26x512
#
# 如果后续重新生成 Top_vivado.sv 后模块名变化，需要重新核对这些 REF_NAME。
# ============================================================

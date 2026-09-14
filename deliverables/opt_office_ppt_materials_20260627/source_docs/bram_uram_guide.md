# BRAM 和 URAM 级联/并联指南

## 方法 A：Chisel SyncReadMem + Vivado 约束（自动推断）

### Chisel 代码
```scala
// 示例：2K x 96 位存储器
val mem = SyncReadMem(2048, UInt(96.W))

// 读写操作
val rdata = mem.read(raddr, ren)
when(wen) {
  mem.write(waddr, wdata)
}
```

### Vivado 约束
```tcl
# 强制使用 BRAM
set_property RAM_STYLE BLOCK [get_cells -hierarchical -filter {NAME =~ "*mem*"}]

# 强制使用 URAM
set_property RAM_STYLE ULTRA [get_cells -hierarchical -filter {NAME =~ "*mem*"}]

# 控制分解方式
set_property RAM_DECOMP power [get_cells mem_reg]  # 优化功耗
set_property RAM_DECOMP area [get_cells mem_reg]   # 优化面积
```

**限制**：
- Vivado 自动决定如何级联/并联
- 对于超宽位宽（如 512 位），可能无法正确映射到 URAM
- 无法精确控制级联方式

---

## 方法 B：手动拆分（推荐用于宽位宽）

### 并联示例：实现 1K x 144 位存储器

```scala
// 拆分为 2 个 1K x 72 位
val mem0 = SyncReadMem(1024, UInt(72.W))
val mem1 = SyncReadMem(1024, UInt(72.W))

// 写入
when(wen) {
  mem0.write(waddr, wdata(71, 0))
  mem1.write(waddr, wdata(143, 72))
}

// 读取
val rdata0 = mem0.read(raddr, ren)
val rdata1 = mem1.read(raddr, ren)
val rdata = Cat(rdata1, rdata0)  // 拼接为 144 位
```

### 级联示例：实现 8K x 72 位存储器

```scala
// 拆分为 2 个 4K x 72 位
val mem0 = SyncReadMem(4096, UInt(72.W))
val mem1 = SyncReadMem(4096, UInt(72.W))

// 地址高位用于选择哪个存储器
val sel = addr(12)  // bit 12 用于选择

// 写入
when(wen) {
  when(sel === 0.U) {
    mem0.write(addr(11, 0), wdata)
  }.otherwise {
    mem1.write(addr(11, 0), wdata)
  }
}

// 读取
val rdata0 = mem0.read(addr(11, 0), ren && sel === 0.U)
val rdata1 = mem1.read(addr(11, 0), ren && sel === 1.U)
val rdata = Mux(RegNext(sel), rdata1, rdata0)
```

---

## 方法 C：使用 BlackBox 例化 Xilinx IP（完全控制）

### 步骤 1：定义 BlackBox

```scala
// URAM 级联 BlackBox（8K x 72 位）
class URAM_Cascade_8Kx72 extends BlackBox {
  val io = IO(new Bundle {
    val clka = Input(Clock())
    val ena = Input(Bool())
    val wea = Input(UInt(8.W))  // 字节写使能
    val addra = Input(UInt(13.W))  // 8K = 2^13
    val dina = Input(UInt(72.W))
    val douta = Output(UInt(72.W))
  })
}

// BRAM 并联 BlackBox（1K x 144 位）
class BRAM_Parallel_1Kx144 extends BlackBox {
  val io = IO(new Bundle {
    val clka = Input(Clock())
    val ena = Input(Bool())
    val wea = Input(UInt(18.W))  // 18 字节写使能
    val addra = Input(UInt(10.W))  // 1K = 2^10
    val dina = Input(UInt(144.W))
    val douta = Output(UInt(144.W))
  })
}
```

### 步骤 2：创建对应的 Verilog 模块

```verilog
// URAM_Cascade_8Kx72.v
module URAM_Cascade_8Kx72 (
  input clka,
  input ena,
  input [7:0] wea,
  input [12:0] addra,
  input [71:0] dina,
  output [71:0] douta
);

// 第一个 URAM（地址 0-4095）
URAM288 #(
  .CASCADE_ORDER_A("FIRST"),
  .BWE_MODE_A("PARITY_INTERLEAVED"),
  .NUM_UNIQUE_SELF_ADDR_A(2),
  .NUM_URAM_IN_MATRIX(2)
) uram0 (
  .CLK(clka),
  .EN_A(ena),
  .ADDR_A(addra[11:0]),
  .BWE_A(wea),
  .DIN_A(dina),
  .DOUT_A(dout0),
  .CAS_OUT_ADDR_A(cas_addr),
  .CAS_OUT_DIN_A(cas_din),
  .CAS_OUT_DOUT_A(cas_dout),
  // ... 其他端口
);

// 第二个 URAM（地址 4096-8191）
URAM288 #(
  .CASCADE_ORDER_A("LAST"),
  .BWE_MODE_A("PARITY_INTERLEAVED"),
  .NUM_UNIQUE_SELF_ADDR_A(2),
  .NUM_URAM_IN_MATRIX(2)
) uram1 (
  .CLK(clka),
  .EN_A(ena),
  .ADDR_A(addra[11:0]),
  .BWE_A(wea),
  .DIN_A(dina),
  .DOUT_A(dout1),
  .CAS_IN_ADDR_A(cas_addr),
  .CAS_IN_DIN_A(cas_din),
  .CAS_IN_DOUT_A(cas_dout),
  // ... 其他端口
);

// 根据地址高位选择输出
assign douta = addra[12] ? dout1 : dout0;

endmodule
```

### 步骤 3：在 Chisel 中使用

```scala
val uram_cascade = Module(new URAM_Cascade_8Kx72)
uram_cascade.io.clka := clock
uram_cascade.io.ena := enable
uram_cascade.io.wea := write_enable
uram_cascade.io.addra := address
uram_cascade.io.dina := write_data
val read_data = uram_cascade.io.douta
```

---

## 针对 Qwen2 加速器的具体建议

### 当前问题
从综合日志看到：
- VCache: 4K x 512 位 → 无法映射到 URAM（位宽超限）
- KCache: 4K x 512 位 → 无法映射到 URAM（位宽超限）

### 解决方案：手动拆分为多个 URAM

```scala
// VCache: 4K x 512 位 = 8 个 4K x 64 位 URAM
class VCache extends Module {
  val io = IO(new Bundle {
    val addr = Input(UInt(12.W))
    val wdata = Input(UInt(512.W))
    val rdata = Output(UInt(512.W))
    val wen = Input(Bool())
    val ren = Input(Bool())
  })

  // 拆分为 8 个 64 位宽的 URAM
  val mems = Seq.fill(8)(SyncReadMem(4096, UInt(64.W)))

  // 写入：并联写入所有 URAM
  when(io.wen) {
    for (i <- 0 until 8) {
      mems(i).write(io.addr, io.wdata((i+1)*64-1, i*64))
    }
  }

  // 读取：并联读取所有 URAM
  val rdatas = mems.map(_.read(io.addr, io.ren))
  io.rdata := Cat(rdatas.reverse)
}
```

### 对应的约束文件

```tcl
# 强制每个 mem 使用 URAM
set_property RAM_STYLE ULTRA [get_cells -hierarchical -filter {NAME =~ "*VCache*mems*"}]
set_property RAM_STYLE ULTRA [get_cells -hierarchical -filter {NAME =~ "*KCache*mems*"}]

# 如果需要级联（深度 > 4K），设置级联高度
set_property CASCADE_HEIGHT 2 [get_cells -hierarchical -filter {REF_NAME == URAM288}]
```

---

## 验证方法

### 1. 查看综合报告
```bash
# 查看 BRAM/URAM 使用情况
grep -A 20 "BLOCKRAM" utilization.rpt
grep -A 10 "URAM" utilization.rpt
```

### 2. 查看原语报告
```tcl
# 在 Vivado TCL 控制台
report_utilization -cells [get_cells -hierarchical -filter {REF_NAME == RAMB36E2}]
report_utilization -cells [get_cells -hierarchical -filter {REF_NAME == URAM288}]
```

### 3. 查看级联连接
```tcl
# 查看 URAM 级联连接
get_nets -hierarchical -filter {NAME =~ "*CAS_OUT*"}
```

---

## 常见问题

### Q1: 为什么 Vivado 没有使用 URAM？
**A:** 可能原因：
1. 位宽超过 72 位（需要手动拆分）
2. 深度不是 4K 的倍数
3. 读写端口配置不符合 URAM 要求
4. 没有设置 RAM_STYLE ULTRA 约束

### Q2: 如何确定需要多少个 BRAM/URAM？
**A:** 计算公式：
- BRAM: `需要数量 = ceil(深度/最大深度) * ceil(位宽/最大位宽)`
- URAM: `需要数量 = ceil(深度/4096) * ceil(位宽/72)`

例如：8K x 512 位
- URAM: `ceil(8192/4096) * ceil(512/72) = 2 * 8 = 16 个`

### Q3: 级联和并联可以同时使用吗？
**A:** 可以！例如 8K x 144 位：
- 深度方向：2 个 URAM 级联（4K → 8K）
- 位宽方向：2 个 URAM 并联（72 → 144）
- 总共需要：2 x 2 = 4 个 URAM

---

## 推荐阅读

1. Xilinx UG573 - UltraScale Architecture Memory Resources
2. Xilinx UG574 - UltraScale Architecture Configurable Logic Block
3. Vivado Design Suite User Guide: Synthesis (UG901)

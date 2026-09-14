# 片上权重存储实现方案

## 问题总结

当前设计使用片外权重存储，导致 URAM/BRAM 使用量远低于前期评估（26 vs 768 个 URAM）。

## 方案对比

### 当前方案：片外存储
- 权重存储：片外 DDR/HBM
- URAM 使用：26 个（仅数据缓冲）
- 带宽需求：~3.6 GB/s
- 优点：设计简单，灵活
- 缺点：性能受限，功耗高

### 目标方案：片上存储
- 权重存储：片上 URAM
- URAM 使用：768 个（权重） + 26 个（数据） = 794 个
- 带宽需求：片上高速访问
- 优点：高性能，低延迟
- 缺点：需要大量 URAM，设计复杂

## 实现步骤

### 步骤 1：添加权重存储模块

为每个线性层添加权重存储器。以 QKVLinear 为例：

```scala
// QKVLinear/WeightMem.scala
package QKVLinear

import chisel3._
import chisel3.util._
import QKVLinear.Param._

class WeightMem extends Module {
  val io = IO(new Bundle {
    // 权重加载接口（初始化时使用）
    val load_en = Input(Bool())
    val load_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val load_data = Input(UInt(WMEM_WIDTH.W))

    // 权重读取接口（计算时使用）
    val read_en = Input(Bool())
    val read_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val read_data = Output(UInt(WMEM_WIDTH.W))
  })

  // 方案 A：使用 Chisel SyncReadMem（让 Vivado 自动映射）
  val weight_mem = SyncReadMem(WMEM_DEPTH, UInt(WMEM_WIDTH.W))

  // 写入（加载权重）
  when(io.load_en) {
    weight_mem.write(io.load_addr, io.load_data)
  }

  // 读取（计算时）
  io.read_data := weight_mem.read(io.read_addr, io.read_en)
}
```

**存储器规格：**
- 深度：49,152
- 位宽：288 位
- 容量：14.2 Mb = 1.68 MB (8位) 或 6.72 MB (32位)

**URAM 映射：**
- 每个 URAM：4K × 72 位
- 位宽方向：288 / 72 = 4 个 URAM 并联
- 深度方向：49,152 / 4,096 = 12 个 URAM 级联
- **总需求：4 × 12 = 48 个 URAM**

但是 Vivado 可能无法自动进行 12 级级联。需要手动拆分：

```scala
// 方案 B：手动拆分为多个 4K 深度的存储器
class WeightMem extends Module {
  val io = IO(new Bundle {
    val load_en = Input(Bool())
    val load_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val load_data = Input(UInt(WMEM_WIDTH.W))

    val read_en = Input(Bool())
    val read_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val read_data = Output(UInt(WMEM_WIDTH.W))
  })

  // 拆分为 12 个 4K × 288 的存储器
  val NUM_BANKS = 12
  val BANK_DEPTH = 4096

  val banks = Seq.fill(NUM_BANKS)(SyncReadMem(BANK_DEPTH, UInt(WMEM_WIDTH.W)))

  // 地址解码
  val bank_sel = io.load_addr(15, 12)  // 高 4 位选择 bank
  val bank_addr = io.load_addr(11, 0)  // 低 12 位是 bank 内地址

  // 写入
  when(io.load_en) {
    banks(bank_sel).write(bank_addr, io.load_data)
  }

  // 读取
  val read_bank_sel = io.read_addr(15, 12)
  val read_bank_addr = io.read_addr(11, 0)

  val read_datas = banks.map(_.read(read_bank_addr, io.read_en))
  io.read_data := read_datas(RegNext(read_bank_sel))
}
```

### 步骤 2：修改 LoadW 模块

```scala
// QKVLinear/LoadW.scala (修改后)
class LoadW extends Module {
  val io = IO(new Bundle {
    // 权重加载接口（初始化）
    val init_mode = Input(Bool())
    val init_data = Input(UInt(WMEM_WIDTH.W))

    // 权重读取接口（计算）
    val update = Input(Bool())
    val st = Input(Bool())

    val data_out = Output(UInt(WMEM_WIDTH.W))
    val data_out_valid = Output(Bool())
  })

  // 实例化权重存储器
  val weight_mem = Module(new WeightMem)

  // 地址生成逻辑（同之前）
  val addr = (row_cnt + rowblock_cnt * ROW.U) * COLBLOCK.U + colblock_cnt

  // 初始化模式：加载权重
  weight_mem.io.load_en := io.init_mode
  weight_mem.io.load_addr := addr
  weight_mem.io.load_data := io.init_data

  // 计算模式：读取权重
  weight_mem.io.read_en := loading && !io.init_mode
  weight_mem.io.read_addr := addr

  io.data_out := weight_mem.io.read_data
  io.data_out_valid := RegNext(RegNext(loading && !io.init_mode, false.B), false.B)
}
```

### 步骤 3：修改顶层接口

```scala
// Top.scala (修改后)
class Top extends Module {
  val io = IO(new Bundle {
    // 添加权重加载模式控制
    val weight_init_mode = Input(Bool())

    // 权重输入（初始化时使用）
    val qkv_w_in = Input(UInt(QKVParam.WMEM_WIDTH.W))
    val out_w_in = Input(UInt(OutParam.WMEM_WIDTH.W))
    val ffnup_w_in = Input(UInt(FFNUpParam.WMEM_WIDTH.W))
    val ffndown_w_in = Input(UInt(FFNDownParam.WMEM_WIDTH.W))

    // ... 其他端口
  })

  // 传递初始化模式到各个模块
  qkvlinear.io.weight_init_mode := io.weight_init_mode
  outlinear.io.weight_init_mode := io.weight_init_mode
  ffnup.io.weight_init_mode := io.weight_init_mode
  ffndown.io.weight_init_mode := io.weight_init_mode
}
```

### 步骤 4：添加约束

```tcl
# constraints_with_weight_storage.xdc

# 强制权重存储器使用 URAM
set_property RAM_STYLE ULTRA [get_cells -hierarchical -filter {NAME =~ "*weight_mem*banks*"}]

# 设置 URAM 级联（如果需要）
set_property CASCADE_HEIGHT 1 [get_cells -hierarchical -filter {REF_NAME == URAM288 && NAME =~ "*weight_mem*"}]
```

## 资源使用预估

### 修改后的资源使用

| 模块 | URAM (权重) | URAM (数据) | 总 URAM |
|------|------------|------------|---------|
| QKVLinear | 192 | 8 | 200 |
| OutLinear | 64 | 8 | 72 |
| FFNUp | 256 | 8 | 264 |
| FFNDown | 256 | 8 | 264 |
| 其他 | 0 | 10 | 10 |
| **总计** | **768** | **42** | **810** |

**VU9P 容量：** 960 个 URAM → 利用率 84% ✓

## 实现难点

### 难点 1：URAM 位宽限制

URAM 最大位宽 72 位，而权重位宽 288 位，需要 4 个 URAM 并联。

**解决方案：** 手动拆分为 4 个 72 位宽的存储器

```scala
val NUM_SLICES = 4
val SLICE_WIDTH = 72

val weight_slices = Seq.fill(NUM_SLICES)(
  SyncReadMem(BANK_DEPTH, UInt(SLICE_WIDTH.W))
)

// 写入
for (i <- 0 until NUM_SLICES) {
  when(io.load_en) {
    weight_slices(i).write(
      bank_addr,
      io.load_data((i+1)*SLICE_WIDTH-1, i*SLICE_WIDTH)
    )
  }
}

// 读取
val read_slices = weight_slices.map(_.read(read_bank_addr, io.read_en))
io.read_data := Cat(read_slices.reverse)
```

### 难点 2：深度超过 4K

QKVLinear 权重深度 49,152 > 4K，需要级联或分 bank。

**解决方案：** 分为 12 个 bank，每个 4K 深度

### 难点 3：初始化时间

27MB 权重需要较长时间加载。

**计算：**
- 权重总量：27 MB = 226,492,416 位
- 每周期加载：288 位
- 需要周期数：226,492,416 / 288 = 786,432 周期
- 时间（100MHz）：7.86 ms

**优化方案：**
- 使用更宽的加载接口（如 1024 位）
- 并行加载多个模块的权重

## 推荐方案

### 短期方案：保持片外存储
- 适用于功能验证和原型开发
- 需要确保外部存储器带宽足够
- 添加性能监控，测量实际带宽需求

### 长期方案：实现片上存储
- 适用于最终产品和性能优化
- 分阶段实现：
  1. 先实现一个模块（如 QKVLinear）
  2. 验证 URAM 映射和性能
  3. 推广到其他模块

## 验证方法

### 1. 资源使用验证
```bash
# 综合后检查 URAM 使用量
grep "URAM" utilization.rpt
# 应该看到约 800 个 URAM
```

### 2. 功能验证
```scala
// 测试权重加载和读取
// 1. 加载权重
// 2. 读取并验证
// 3. 进行计算并检查结果
```

### 3. 性能验证
```
# 测量吞吐量
# 对比片外 vs 片上存储的性能差异
```

## 参考资料

- Xilinx UG573: UltraScale Architecture Memory Resources
- Xilinx UG949: UltraFast Design Methodology Guide
- 当前项目：docs/bram_uram_guide.md

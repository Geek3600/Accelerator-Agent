# OPT-125M模型量化方案

## LayerNorm1
* 输入精度：FP32
* 输出精度：INT8
说明：这是量化版 LayerNorm，它把 LN 的输出直接作为后续 INT8 激活输入。


## QKVLinear
* 形式：W8A8B8O8Linear
* 权重精度：INT8
* 激活输入精度：INT8
* 输出精度：INT8
说明：Q/K/V 三个线性层都是全 INT8 线性层。



## Q·K（DM1）
* 形式：BMM_S8T_S8N_F32T
* 输入精度：INT8 × INT8
* 累加/输出精度：FP32
说明：
* Q 和 K 都是 INT8
* 点积累加时提升到 FP32
* 输出的是 attention logits（浮点）


## Softmax
* 模块：softmax
* 输入精度：FP32
* 输出精度：FP32
说明：
Softmax 本身在浮点域完成
因为 softmax 对数值稳定性要求高，所以没有 INT8 化




## P * V （DM2）
* 形式：BMM_S8T_S8N_S8T
* 输入精度：
* attention probs：先由 softmax 的 FP32 结果量化到 INT8
* V：INT8
* 计算精度：INT8 × INT8
* 输出精度：INT8
说明：
softmax 输出先量化成 INT8
然后和 INT8 的 V 做乘法
最终得到 INT8 的 attention 输出



## OutLinear
* 形式：W8A8BFP32OFP32Linear
* 权重精度：INT8
* 激活输入精度：INT8
* 输出精度：FP32
说明：
这是 attention 后的输出投影
虽然输入和权重都是 INT8，但输出会转回 FP32




## ResAdd
* 模块：attention 后残差相加
* 输入精度：FP32
* 输出精度：FP32
说明：
残差加法在浮点域完成
不是 INT8 残差加法



## LayerNorm2
* 模块：final_layer_norm
* 形式：LayerNormQ
* 输入精度：FP32
* 输出精度：INT8
说明：
FFN 前的第二个量化 LayerNorm
输出直接作为 FFN 的 INT8 激活输入



## FFNUp
* 模块：fc1
* 形式：W8A8B8O8LinearReLU
* 权重精度：INT8
* 激活输入精度：INT8
* 输出精度：INT8
说明：
FFN 第一层（升维）
是 INT8 线性层
并且和后面的 ReLU 融合在一起



## RELU
* 模块：fc1 后激活
* 输入精度：INT8（在该实现里与 fc1 融合）
* 输出精度：INT8
说明：
你的图里 fc1 是 W8A8B8O8LinearReLU
所以 ReLU 是融合在这个算子内部的
从系统角度看，它前后仍然可以视为 INT8



## FFNDown
* 模块：fc2
* 形式：W8A8BFP32OFP32Linear
* 权重精度：INT8
* 激活输入精度：INT8
* 输出精度：FP32
说明：
FFN 第二层（降维）
输入仍是 INT8
但输出转回 FP32



## ResAdd2
* 模块：FFN 后残差相加
* 输入精度：FP32
* 输出精度：FP32
说明：
最后的残差加法仍在浮点域完成


| 模块         | 输入精度        | 权重精度 | 输出精度      |
| ----------  | -----------    | ----    | ---------   |
1 | LayerNorm   | FP32           | -       | INT8        |
2 | QKVLinear   | INT8           | INT8    | INT8        |
3 | Q·K         | INT8 × INT8    | -       | FP32        |
4 | Softmax     | FP32           | -       | FP32        |
5 | DM2（P·V）   | INT8 × INT8    | -       | INT8        |
6 | OutLinear   | INT8           | INT8    | FP32        |
7 | ResAdd      | FP32           | -       | FP32        |  
8 | LayerNorm2  | FP32           | -       | INT8        |
9 | FFNUp       | INT8           | INT8    | INT8        |
10| ReLU        | INT8           | -       | INT8        |
11| FFNDown     | INT8           | INT8    | FP32        |
12| ResAdd2     | FP32           | -       | FP32        |

# 材料包说明

本目录用于制作“OPT + Office”项目 PPT。内容只面向当前项目工程，不包含论文方法论和 agent 框架内容。

## 目录内容

```text
OPT_Office_项目内容总结.md
PPT页纲建议.md
算核库_工具链_部署清单.md
README_材料包说明.md
```

后续打包时会附带以下目录：

```text
source_docs/
kernel_library/
toolchain/
deployment/
cases_and_manifests/
vivado_ip/
```

## 使用建议

- 做 PPT 时优先阅读 `OPT_Office_项目内容总结.md`。
- 需要拆页时直接参考 `PPT页纲建议.md`。
- 需要列附件和工程资产时参考 `算核库_工具链_部署清单.md`。

## 大文件说明

正式部署用的大文件不放入本材料包：

- bitstream；
- DDR image；
- Office runtime tar；
- 模型压缩包；
- Vivado 巨大网表。

这些文件在部署脚本和部署清单中有明确名称和路径，PPT 中只需要展示其作用，不需要随材料包发送。


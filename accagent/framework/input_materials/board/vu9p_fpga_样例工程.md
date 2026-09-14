# xcvu9p fpga板卡的样例工程
* 位置在 hyyuan@10.12.133.23服务器上，目录位置是/home/share/v6.0_9p_cnn_2slr_4core_yolov8
* 里面有ddr和axi wrapper的样例工程，可以参考
* 样例工程 Vivado project 中的具体 part 是 `xcvu9p_CIV-flgb2104-2-i`，来源是：
  * `/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr`
  * `<Option Name="Part" Val="xcvu9p_CIV-flgb2104-2-i"/>`
* Stage 0 必须提取具体 FPGA part，不能只写 VU9P 这种模糊板卡名。
  
# 限制
* 只能读这里的内容，不能修改，因为要保持目录这个作为样例工程的备份
* 不能在/home/share/目录下创建和修改任何新内容，只能在我们自己的用户目录hyyuan/workspace下进行工作

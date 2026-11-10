# R1 原始运行与复盘

- `section20/`：修改前四次规则控制基线，完整实时观测、轨迹、事件、原始summary和源身份；全部符合§2.0。
- `section20_final/`：当前源码真值隔离后的四次复核，单独保留，不覆盖初次记录。
- `standins/`：明确标注的离线替身/流程检查，任务ID均含OFFLINE-STANDIN；**不是新Lux3D任务，不能计为真实Lux成功**。单批真B替身与追加一份真B替身均因low_margin停车；两批全拒绝验证12份后安全停止且无第三批。
- `frozen_before_r1/`：R1以前的原始场景配置；只有purpose被负责人要求改变，原几何、太阳和门槛保持。
- `logs/`：全部测试和运行日志，包括失败；`connectivity.json`只记录实际联网错误，不含密钥。

[preservation_audit.json](preservation_audit.json)核对12个运行的源码身份、603份原始文件、58份首眼重放源文件及四次完整轨迹重现；`restore_standin_inputs.py`按共享清单恢复保存命令依赖的首眼源目录，无需重复复制资产。

每个运行的`preservation.json`列出原始文件逐SHA256摘要、原输出位置及匹配实际源码的Git提交。`eval.json`由`build_eval.py`赛后读取真实扫描几何产生；规划器不读取这些复盘结果。路线以5 mm间距检查，车身间隙另用随实测yaw旋转的0.76×0.66 m平面矩形包络计算；这是XY包络，3D接触以原始碰撞记录为准。

```bash
# 安装依赖/恢复LFS与岩石库后，重新生成赛后复盘数字。
.venv/bin/python evidence/reviews/beforestep_r1/build_eval.py

# 如需检查保存请求的原始路径，按SHA恢复离线输入；拒绝覆盖不同字节。
.venv/bin/python evidence/reviews/beforestep_r1/restore_standin_inputs.py
```

完整命令、退出码、预期与每次summary原文在[RESULT_BEFORESTEP_R1](../../../docs/reviews/RESULT_BEFORESTEP_R1.md)。真实Lux主线、逐候选trust反事实和完整真实重放尚未完成，不能根据替身或单元测试宣称主线成立。

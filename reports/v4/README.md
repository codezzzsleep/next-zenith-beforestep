# 先见一步 · 项目报告书 v4

本版将“一张照片交给 Lux3D，拿回整块石头的3D模型”放在开篇，展示它与轮腿在同一条月面路线上的作用，并保留失败、停车和适用边界。第3/7页更新为当前半自由任务的真实截图和既有录屏抽帧：观察点停车、原GLB转面、带3D参考驾驶、逐腿跨越与抵达。

[正式PDF](report.pdf) · [全册预览](report.contact.jpg) · [资料出处](SOURCES.md) · [验收记录](verification.json)

报告、游戏与实验均为MuJoCo仿真。报告没有触发新的Lux3D生成；门槛石来自可见面，展示路线与原R1/R2/R3实验分别计数。

## 重建

Python 3.12与Linux Fontconfig/Pango可运行。中文字体、图片、21张V3原图、spec与PDF引擎均随本目录提供，重建不读取机器私有记忆或临时截图。Ubuntu/Debian需要 `python3-venv libpango-1.0-0 libpangocairo-1.0-0 libharfbuzz-subset0 libfontconfig1 fonts-dejavu-core`。

只下载报告源包：

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --filter=blob:none --sparse https://github.com/codezzzsleep/next-zenith-beforestep.git beforestep-report
cd beforestep-report
git sparse-checkout set reports/v4
python3 -m venv .venv
.venv/bin/pip install -r reports/v4/requirements.txt
REPORT_PY="$PWD/.venv/bin/python" bash reports/v4/build.sh
```

结果在 `reports/v4/out/report.pdf`，同目录输出HTML、分页信息、版面/内容引用审计与全册预览。`report.pdf`是本次提交的成稿；数字依据在 `facts-snapshot.json`，素材SHA在 `asset-sources.json`。字体缺新字符时，从 `fonts/sources.json` 的固定上游URL取三份原OTF，先运行 `tools/build_fonts.py --source-dir 原OTF目录`，再构建。

自动审计检查版面边界和110个来源单元的引用。改写与图表替换需要人工判断；本版原文、图表分母、真值/生成区别、后验修改与游玩边界均另外复核。重建验证比较最终文字和逐页渲染，PDF二进制哈希用于下载完整性，不能保证跨系统生成的字节完全相同。

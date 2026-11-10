# 自己摆石头，再在本地验证

沙盒使用现有扫描岩石的真实占地。浏览器里的视线遮挡和太阳黑影是俯视几何近似，路线使用正式流程的 5 cm 格子、转向节点、直线边和机器人余量。“想一想”只复用场景组中同扫描岩石实际生成并通过自检的候选；没有可复用准入候选，附近未知继续保留。移动或旋转会变换既有候选，不会发起新的生成。

路线动画不做物理仿真；车身包络压到真实占地是规划诊断，不是 MuJoCo 碰撞结果。关卡模式提供完整真实物理运行。整组首眼定性一致性检查会逐项报告不一致，不把轻量沙盒等同于 RGB-D 传感器与物理预演。

## 导出与运行

点击“导出场景 JSON”，把文件复制到 `config/scenes/`。文件名必须是 JSON 中 `id` 加 `.json`。保留 `terrain`、`sun`、`asset_cache_precision`、起点、首眼和终点字段。安装锁定依赖，保持 MuJoCo 3.17.0，运行命令中的 `<场景id>` 使用导出的 id。

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-deps -e .
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene <场景id> \
  --controller-model rules --policy imagination --imagine truth \
  --out outputs/user_scenes/<场景id>-truth
```

这次不花钱，使用真值形状做独立可通性检验。要验证真实扫描替身的配准、自检、预演和执行全链，使用当前源码已通过的回归记录：

```bash
MUJOCO_GL=egl .venv/bin/python ops/run_suite_imagination.py \
  --scene <场景id> --mode standin --out outputs/user_scenes/<场景id>-standin \
  --regression evidence/suite/regressions/B1-crater-target/regression.json
```

替身会明确记录 `not_real_lux=true`，不能记作真实 Lux3D 收益。

真实 Lux3D 需要自己的密钥和付费额度。先跑四种非 Lux 对照及完整替身链，在新结果文件记录预期，再准备首眼请求：

```bash
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene <场景id> \
  --controller-model rules --policy imagination --imagine lux \
  --out outputs/user_scenes/<场景id>-real
```

退出码 10 表示等待生成，不是完成。读取该运行 `imagination/NEED_LUX3D.json`，逐份处理其中的请求。密钥放在仓库外的 `.env`，支持 `API_key`，不要写进命令或提交。首次提交与恢复查询分别使用：

```bash
.venv/bin/python -m beforestep generate --request <请求文件> \
  --env-file <仓库外.env> --submit --wait
.venv/bin/python -m beforestep generate --request <同一请求文件> \
  --env-file <仓库外.env> --wait
```

每个身份先落账本，已知或不确定任务只查询，不重复提交。任务终态后用原运行命令恢复；需要第二眼时继续按原冻结协议，单图六份零准入最多同输入再追加六份，仍零就安全停车。不要把局部候选准入当成导航成功。

## 证据恢复

每个正式场景的 `evidence/suite/scenes/<场景id>/manifest.json` 列出 SHA、运行身份和精简数据位置。精简集保留原字节，压缩对象可以恢复到原相对路径：

```bash
.venv/bin/python ops/restore_suite_scene.py \
  --manifest evidence/suite/scenes/<场景id>/manifest.json
```

完整外部 tar 包的位置与 SHA 在同一清单和 R2 结果中；取得包后追加 `--archive <完整tar.gz>` 可恢复全部原文件与原 GLB。恢复脚本校验字节、拒绝覆盖不同内容。真实运行身份可直接查看 `runs/<策略>/run_identity.json`，无需解包。

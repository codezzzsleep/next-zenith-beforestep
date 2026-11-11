"""Create evidence-linked video scripts, posts and a submission checklist."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    facts = json.loads((ROOT / 'evidence/award/facts.json').read_text())
    original = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    out = ROOT / 'evidence/video/award'
    out.mkdir(parents=True, exist_ok=True)
    items = []
    for relative in ['site/media/award/first.png', 'site/media/award/second.png',
                     'site/media/award/asset-iterations.png', 'evidence/award/browser/award-local-desktop-1440.png',
                     'evidence/award/browser/award-local-two-shadows.png', 'evidence/award/browser/award-local-mobile-390.png',
                     'evidence/award/browser/award-final-local-choices.png', 'evidence/award/browser/award-final-local-failures.png',
                     'evidence/award/browser/award-final-local-revision.png', 'evidence/award/facts.json',
                     'evidence/award/observations.json', 'evidence/award/asset-iterations/manifest.json',
                     'evidence/video/index.json']:
        source = ROOT / relative
        assert source.is_file(), relative
        name = source.name if source.name not in ('index.json', 'manifest.json') else ('run-data-index.json' if source.name == 'index.json' else 'asset-iterations-manifest.json')
        target = out / name
        shutil.copy2(source, target)
        items.append({'path': str(target.relative_to(ROOT)), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                      'source_path': relative, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    frozen, held = facts['frozen_revision'], facts['heldout_revision']
    scope = f"最终 v3 已知场景：{frozen['arrived']}到达、{frozen['safe_stop']}停车、{frozen['collisions']}碰撞；指定留出：{held['arrived']}到达、{held['safe_stop']}停车、{held['collisions']}碰撞。"
    collision_runs = {r['scene']: r['runs']['imagination']['run'] for r in original['scenes']
                      if r['scene'] in original['imagination_collision_scenes']}
    shots = [
        ('真实机器人运行', '负责人用零付费命令录制 MuJoCo 被动查看器的真实独立执行与旁边的网站。',
         'ops/award_record_screen.py; evidence/video/index.json; evidence/reviews/beforestep_r1/lux/original_b/traj.npz',
         '看不见的那一面，先在想象里走一遍。', True),
        ('两种影子', '固定首眼太阳黑影参考，拖动到真实第二眼，地图随原观测变化。',
         'evidence/video/award/first.png; evidence/video/award/second.png; site/data/award-observations.json',
         '太阳照不到的地方，换位置也照不亮；视线遮挡，换一个真实位置再看。', True),
        ('三种选择与测深对照', '并排真实轨迹，揭晓保守、乐观、Lux 与 see-dark 原终态。',
         'evidence/video/award/award-final-local-choices.png; site/data/demo.json',
         '原窄道：保守停车，乐观碰撞，真实 Lux 到达；黑影测深对照也到达。', True),
        ('Lux3D 核心链', '转动真实候选，展示配准、自检、候选完整预演与独立执行。',
         'site/index.html#award-lux-pipeline; evidence/award/facts.json; evidence/video/index.json',
         f"原批 {facts['original_unique_tasks']} 个唯一任务，{facts['original_generated_glb']} 份 GLB；{facts['original_admitted']} 准入，{facts['original_rejected']} 拒绝。", True),
        ('两次真实碰撞及原因', '先显示 F1_020 被完全遮住的 C，再显示 F3_004 通过正面自检但偏短的 B 背面；锚点间隙同时呈现。',
         'evidence/video/award/award-final-local-failures.png; '+ '; '.join(collision_runs.values()) + '; evidence/reviews/beforestep_r3/failure-facts.json',
         'F1_020：C 从未被看见；F3_004：背面偏短。锚点三维间隙47.541 mm，二维包络间隙0 mm，成功不稳健。', True),
        ('赛后修订与适用范围', '展示五栏表、留出单独成表，oldv2 碰撞保持可见；停下不当作效率优势。',
         'evidence/video/award/award-final-local-revision.png; evidence/reviews/beforestep_r3/summary.json',
         '想象只解释太阳的影子；视线的影子，再看一眼。'+scope+' oldv2 曾在F1_003碰撞。', True),
        ('被拒候选的反事实', '回放原批被拒干预，展示完整前缀核验；修订批按已知与留出分开。',
         'site/index.html#counterfactual; evidence/suite/summary.json; evidence/award/facts.json; evidence/video/index.json',
         f"原批被拒干预 {facts['original_counterfactuals']['collisions']}/{facts['original_counterfactuals']['executed']} 碰撞；修订已知批 {facts['revision_new_counterfactuals_by_scope']['known_frozen']['executed']} 份另列。", True),
        ('证据与入口', '显示真实资产迭代图、仓库、可体验网页、报告 PDF；新演示若执行加上不参与结论标注。',
         'evidence/video/award/asset-iterations.png; docs/hackathon-submission.md; site/en.html',
         '原结果、失败、输入、生成资产与源码都公开。赛后补充演示不参与结论、不作为泛化证据。', True)]
    def timestamp(seconds):
        return f'{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d},000'
    for length, durations in [(90, [8, 12, 16, 10, 14, 12, 10, 8]), (45, [4, 6, 8, 5, 7, 6, 5, 4])]:
        assert sum(durations) == length
        text = f'# {length} 秒分镜\n\n每镜均取真实记录；视频由负责人录屏、渲染与剪辑。字幕数字来自 `evidence/award/facts.json` 和原失败证据，不从旧视频沿用结论。\n\n| 镜号 | 时长 | 画面 | 来源文件 | 字幕 | 负责人录屏 |\n| --- | --- | --- | --- | --- | --- |\n'
        srt, elapsed = [], 0
        for i, ((title, picture, source, subtitle, screen), duration) in enumerate(zip(shots, durations), 1):
            text += f'| {i} | {duration}s | {title}：{picture} | `{source}` | {subtitle} | 是 |\n'
            srt.append(f'{i}\n{timestamp(elapsed)} --> {timestamp(elapsed+duration)}\n{subtitle}\n')
            elapsed += duration
        (out / f'storyboard-{length}s.md').write_text(text)
        (out / f'subtitles-{length}s.srt').write_text('\n'.join(srt))
    command = 'PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src MUJOCO_GL=glfw /usr/bin/python3 ops/award_record_screen.py'
    (out / 'record-screen.md').write_text('''# 真实运行录屏入口

在有桌面的本机或负责人工作站，安装仓库依赖并从仓库根运行。此命令复用原首眼 Lux 资产，重新自检、完整物理预演与独立执行，不创建付费任务，也不编码 Demo。网页与 MuJoCo 被动查看器分别打开，负责人录屏。

```bash
''' + command + '''
```

上述 PYTHONPATH 是本机已经核验的依赖目录；在负责人工作站激活 README 的虚拟环境后使用 `MUJOCO_GL=glfw python ops/award_record_screen.py`。每次使用新的输出目录，默认自动以 UTC 时刻命名。

`--headless` 用于无桌面验证实际重用链；录屏时省略它。GUI 需要桌面/OpenGL，服务器上无 DISPLAY 的验证不冒充 GUI 验收。实际传感器重新渲染若与原字节不一致，会保存 NEED_LUX3D 并停止；该命令不加载密钥或自动生成，不能用新生成绕过身份核验。

网页轨迹回放与轻量沙盒均有明确标注。新视频由负责人制作，当前旧 mp4 保持历史标识。完整 22 个运行的物理、观测与渲染来源使用 `evidence/video/index.json`，不要从外包代替这些公开数据。
''')
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name != 'index.json' and not any(i['path'] == str(path.relative_to(ROOT)) for i in items):
            items.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (out / 'index.json').write_text(json.dumps({'schema': 'beforestep-award-video-kit/v1', 'items': items,
        'storyboards': [90, 45], 'source_run_index': 'evidence/video/index.json',
        'renderer': 'Project lead; the agent prepared data, scripts and subtitles only.'}, ensure_ascii=False, indent=2) + '\n')
    post = ROOT / 'docs/award-promotion.md'
    images = [i['path'] for i in items if i['path'].endswith('.png') and 'mobile' not in i['path']][:9]
    assert 6 <= len(images) <= 9
    post.write_text(f'''# 传播材料（由负责人发布）

## 小红书：技术版

我做了一台会“先见一步”的月面轮腿机器人：实际 RGB-D → Aholo Lux3D 多候选 → 观测配准与冻结自检 → 完整物理预演 → 独立执行 → 被拒候选反事实。

原批真实生成任务 {facts['original_unique_tasks']} 个、GLB {facts['original_generated_glb']} 份。原窄道 Lux 到达，但预注册场景组也发生两次想象碰撞：一块石头完全藏在视线后，一份背面假设偏短却通过正面自检。原拒绝候选反事实 {facts['original_counterfactuals']['collisions']}/{facts['original_counterfactuals']['executed']} 碰撞。

后来做了“只解释太阳黑影、继续观察视线未知”的赛后修订。{scope} 只有固定留出支持样本外判断，停车不是通行成功。所有失败、输入 SHA、任务、GLB、预演和源码保留。

可体验： https://codezzzsleep.github.io/next-zenith-beforestep/levels.html
源码： https://github.com/codezzzsleep/next-zenith-beforestep
报告： https://codezzzsleep.github.io/next-zenith-beforestep/report.html

#Aholo黑客松
发布后至结果公布前保持公开。

## 小红书：大众版

石头挡住路时，你会直接走、多看一眼，还是先想象它看不见的背面？

我把这个问题做成了能玩的月面实验。机器人面对两种影子：太阳照不到的黑影，以及被岩石挡住的视线。移动相机能改变视线，却不能把太阳黑影照亮。它请 Aholo Lux3D 提出背面的几何假设，再走进完整物理预演，最后才行动。

它有走到终点的记录，也有真的撞上石头的记录。好看的假设不等于正确的背面，所以网页把失败原因、所有选择与真实轨迹一起展示。点一个策略，看看你的选择会发生什么。

体验： https://codezzzsleep.github.io/next-zenith-beforestep/
这是实际仿真实验，不是实机演示；赛后修订与补充演示都有单独标注。

#Aholo黑客松
发布后至结果公布前保持公开。

## 配图（真实观测或实际网页截图）

''' + '\n'.join(f'{i}. [{Path(p).name}](../{p})' for i, p in enumerate(images, 1)) + '''

## 魔搭社区模型页与 Notebook 文本

项目名：BeforeStep / 先见一步。核心是 Aholo Lux3D 真实几何候选、观测自检、全部采纳世界完整预演与独立执行。模型页同时列出规则导航主实验、历史学习控制权重以及失败证据，历史权重不冒充 R3 的控制器。

Notebook 从公开源码安装，使用已有观测与 Lux 结果复现，不要求读者提供生成密钥。入口依次为环境检查、数据 SHA 核验、已记录场景复用、真实轨迹回放和原失败说明。云端新生成是单独可选流程，需要读者自己的额度；默认复现不创建任务。

仓库：https://github.com/codezzzsleep/next-zenith-beforestep
Demo：https://codezzzsleep.github.io/next-zenith-beforestep/
报告：https://codezzzsleep.github.io/next-zenith-beforestep/report.html
模型权重：仓库 `assets/models/`；任务输入与真实候选：`assets/`；视频素材：`evidence/video/award/`。

活动说明：魔搭社区发布经核验后可获 20 小时 Notebook GPU 额度；这里提供说明文本，未声称已领取。负责人发布后填入模型页链接与 Notebook 链接。

模型页链接：负责人待发布；Notebook链接：负责人待发布。小红书链接：负责人待发布。
''')
    stamp = datetime.now(timezone.utc).isoformat()
    (ROOT / 'docs/hackathon-submission.md').write_text(f'''# 黑客松提交核对表

提交截止：2026-11-19 19:00（北京时间）。视频渲染、社交发布与比赛网站提交由负责人完成；Agent 准备并核验可交付材料，不索取发布账号。

| 项目 | 必交/加分 | 链接或明确状态 | 完成者 | 当前核验时间 |
| --- | --- | --- | --- | --- |
| 项目报告书 | 必交 | [在线报告](https://codezzzsleep.github.io/next-zenith-beforestep/report.html) · [PDF](https://codezzzsleep.github.io/next-zenith-beforestep/media/report.pdf)；过程截图与关键资产迭代已纳入 | Agent准备与核验；负责人提交 | {stamp} |
| 完整 Demo 可体验入口 | 必交 | [作品](https://codezzzsleep.github.io/next-zenith-beforestep/) · [真实关卡回放](https://codezzzsleep.github.io/next-zenith-beforestep/levels.html) · [轻量沙盒](https://codezzzsleep.github.io/next-zenith-beforestep/sandbox.html) | Agent发布与核验 | {stamp} |
| 含真实运行画面的视频 | 必交 | 新视频由负责人录屏/渲染/剪辑，待负责人填写最终链接；[完整数据与两版分镜](../evidence/video/award/index.json)已交付。[旧视频](https://codezzzsleep.github.io/next-zenith-beforestep/media/demo.mp4)仅作明确标注的历史参考 | 负责人制作与提交 | {stamp}（素材核验，非新视频完成时间） |
| 项目源代码 | 加分/交付 | [公开仓库](https://github.com/codezzzsleep/next-zenith-beforestep) | Agent维护与核验；负责人提交链接 | {stamp} |
| 小红书 | 加分 | 负责人待发布并填写链接；[两版文案与真实配图](award-promotion.md)齐备，带 `#Aholo黑客松`，结果公布前保持公开 | 负责人 | {stamp}（材料核验） |
| 魔搭模型页/Notebook | 社区奖励 | 负责人待发布并填写链接；[发布说明](award-promotion.md)齐备，核验后可获20小时GPU额度，未声称已领取 | 负责人 | {stamp}（材料核验） |
| 英文摘要 | 国际评委辅助 | [English](https://codezzzsleep.github.io/next-zenith-beforestep/en.html) · [源文本](report-en.md) | Agent准备与核验 | {stamp} |
| 最终比赛网站提交 | 负责人步骤 | 新视频链接补齐后由负责人逐项核对并提交；不把准备好的素材误写成已提交 | 负责人 | 待提交 |

所有必交项目都有材料链接或明确负责人状态；新视频实际文件仍须由负责人完成。不能用旧视频、空链接或素材索引冒充新 Demo 视频已完成。
''')
    print(json.dumps({'video_items': len(items), 'storyboards': [90, 45], 'promotion_images': len(images),
                      'all_sha_recorded': True, 'new_video_rendered': False}))


if __name__ == '__main__':
    main()

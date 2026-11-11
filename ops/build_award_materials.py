"""Create evidence-linked video scripts, posts and a submission checklist."""
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    facts = json.loads((ROOT / 'evidence/award/facts.json').read_text())
    original = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    revised = json.loads((ROOT / 'evidence/reviews/beforestep_r3/summary.json').read_text())
    anchor = json.loads((ROOT / 'evidence/web-assets/anchor.json').read_text())
    failure_facts = json.loads((ROOT / 'evidence/reviews/beforestep_r3/failure-facts.json').read_text())
    out = ROOT / 'evidence/video/award'
    out.mkdir(parents=True, exist_ok=True)
    history = out / 'history/pre-owner-homepage'
    history.mkdir(parents=True, exist_ok=True)
    for name in ('storyboard-90s.md', 'storyboard-45s.md', 'subtitles-90s.srt', 'subtitles-45s.srt', 'record-screen.md', 'index.json'):
        source = out / name
        if source.exists() and not (history / name).exists():
            shutil.copy2(source, history / name)
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
    def outcome_counts(rows, policy):
        return dict(Counter(r['runs'][policy]['summary']['result'] for r in rows))
    decisive = [r for r in original['scenes'] if r['classification'] == 'decisive']
    known_counts = outcome_counts(decisive, 'imagination')
    held_counts = outcome_counts(revised['holdouts'], 'imagination')
    number_sources = {'known_decisive_original': known_counts, 'holdout_original': held_counts,
                      'holdout_final_v3': held, 'known_final_v3': frozen,
                      'original_counterfactuals': facts['original_counterfactuals'],
                      'anchor_gap_published_mm': failure_facts['anchor_clearance_3d_mm'],
                      'anchor_xy_gap_mm': failure_facts['anchor_xy_envelope_clearance_mm'],
                      'sources': ['evidence/suite/summary.json', 'evidence/reviews/beforestep_r3/summary.json',
                                  'evidence/reviews/beforestep_r3/failure-facts.json', 'evidence/web-assets/anchor.json']}
    (out / 'number-sources.json').write_text(json.dumps(number_sources, ensure_ascii=False, indent=2)+'\n')
    gap = f"锚点三维间隙 {number_sources['anchor_gap_published_mm']} mm，二维包络间隙 {number_sources['anchor_xy_gap_mm']} mm，成功不稳健。"
    generated = [r for r in anchor['generated'] if r['provider_status'] == 'ok']
    a1_task = next(r['task_id'] for r in anchor['registration_contexts']
                   if r['target'] == 'T1' and r['sample'] == 'A1')
    a1 = next(r for r in generated if r['task_id'] == a1_task)
    model_source = f"{a1['path']}; " + '; '.join(a1['web_inputs'])
    shots = [
        ('一张真实照片进入 Lux3D', '显示实际上传 JPEG 与同任务生成的整块石头，镜头停在照片和模型之间；录制首页成品或技术报告真实模型查看器。',
         model_source + '; evidence/web-assets/anchor.json; site/report.html#assets',
         '机器人只拍到一面。Lux3D 把这一张照片变成一整块石头。', True),
        ('为什么非想背面不可', '用真实首眼 RGB 与静态 DARK 对照交代低角度太阳，再显示三车原轨迹；不做影子拖动动画。',
         'evidence/video/award/first.png; evidence/web-assets/observations/conservative-look1-dark.png; site/data/demo.json',
         '背光面全黑，车却要从看不见的那一面旁边过。保守停车，乐观碰撞，原 Lux 到达。', True),
        ('高潮：整块石头，转到背面', '在真实模型查看器拖动原任务石头至背面，显示同一照片的多份模型与任务 ID；真值叠合只用提供的配准矩阵，未接好时录制真实独立模型与原背面诊断。',
         model_source + '; evidence/web-assets/models.json; evidence/web-assets/registrations.json; evidence/web-assets/truth/B.glb; site/report.html#assets',
         '这一面，照片从没拍到，是 Lux3D 想出来的。'+gap, True),
        ('想象怎样接受检查', '展示通过与被拒的真实候选及原因，配准叠回观测，再展示十二份完整预演轨迹；录制技术报告与对应终端记录。',
         'evidence/web-assets/registrations.json; evidence/web-assets/anchor.json; site/report.html#award-lux-pipeline; evidence/video/index.json',
         f"原批 {facts['original_generated_glb']} 份 GLB，{facts['original_admitted']} 准入、{facts['original_rejected']} 拒绝；被拒干预 {facts['original_counterfactuals']['collisions']}/{facts['original_counterfactuals']['executed']} 会撞。", True),
        ('真实执行与三车结果', '负责人录制零付费 --reuse-lux 的终端真实观察、自检、预演、执行；同时录制原三车真实回放。无头运行没有窗口，网站回放另开 8081。',
         'ops/award_record_screen.py; evidence/reviews/beforestep_r1/lux/original_b/traj.npz; evidence/video/award/award-final-local-choices.png; site/data/demo.json',
         f"已知决定性 {len(decisive)} 场：原想象 {known_counts.get('arrived',0)} 到达、{known_counts.get('stuck',0)} 停车、{known_counts.get('collision',0)} 碰撞。", True),
        ('两次真实碰撞及原因', '先显示 F1_020 被完全遮住的 C，再显示 F3_004 通过正面自检但偏短的 B 背面；锚点间隙同时呈现。',
         'evidence/video/award/award-final-local-failures.png; '+ '; '.join(collision_runs.values()) + '; evidence/reviews/beforestep_r3/failure-facts.json',
         'F1_020：C 从未被看见；F3_004：背面偏短。'+gap, True),
        ('赛后修订与适用范围', '展示五栏表、留出单独成表，oldv2 碰撞保持可见；停下不当作效率优势。',
         'evidence/video/award/award-final-local-revision.png; evidence/reviews/beforestep_r3/summary.json',
         f"样本外：原想象 {held_counts.get('arrived',0)} 到达、{held_counts.get('stuck',0)} 停车、{held_counts.get('collision',0)} 碰撞；最终 v3 修订 {held['arrived']} 到达、{held['safe_stop']} 停车、{held['collisions']} 碰撞。有效，但不绝对。oldv2 曾在 F1_003 碰撞。", True),
        ('证据与入口', '显示真实资产迭代图、仓库、可体验网页、报告 PDF；新演示若执行加上不参与结论标注。',
         'evidence/video/award/asset-iterations.png; docs/hackathon-submission.md; site/en.html',
         '原结果、失败、输入、生成资产与源码都公开。赛后补充演示不参与结论、不作为泛化证据。', True)]
    def timestamp(seconds):
        return f'{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d},000'
    for length, durations in [(90, [8, 12, 18, 14, 12, 10, 10, 6]), (45, [4, 6, 9, 7, 6, 5, 5, 3])]:
        assert sum(durations) == length
        text = f'# {length} 秒分镜\n\n每镜均取真实记录；视频由负责人录屏、渲染与剪辑。字幕数字来自 `evidence/award/facts.json` 和原失败证据，不从旧视频沿用结论。\n\n| 镜号 | 时长 | 画面 | 来源文件 | 字幕 | 负责人录屏 |\n| --- | --- | --- | --- | --- | --- |\n'
        srt, elapsed = [], 0
        for i, ((title, picture, source, subtitle, screen), duration) in enumerate(zip(shots, durations), 1):
            text += f'| {i} | {duration}s | {title}：{picture} | `{source}` | {subtitle} | 是 |\n'
            srt.append(f'{i}\n{timestamp(elapsed)} --> {timestamp(elapsed+duration)}\n{subtitle}\n')
            elapsed += duration
        (out / f'storyboard-{length}s.md').write_text(text)
        (out / f'subtitles-{length}s.srt').write_text('\n'.join(srt))
    command = 'PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src MUJOCO_GL=egl /usr/bin/python3 -u ops/award_record_screen.py --headless --reuse-lux evidence/reviews/beforestep_r1/lux/original_b'
    (out / 'record-screen.md').write_text('''# 真实运行录屏入口

## 入口一：终端真实无头流程

从仓库根运行下列一条命令。它复用原首眼 Lux 资产，终端打印真实观测、生成任务复用、自检、十二个完整物理预演、独立执行；不产生新付费任务。负责人录制终端。无头运行没有图形窗口，画面来自终端输出与既有离屏帧。

```bash
''' + command + '''
```

上述 PYTHONPATH 是本机已核验的依赖目录。在负责人工作站激活 README 的虚拟环境后使用 `MUJOCO_GL=egl python -u ops/award_record_screen.py --headless --reuse-lux evidence/reviews/beforestep_r1/lux/original_b`。每次使用新的输出目录，默认自动以 UTC 时刻命名。既有实际验证见 `evidence/award/acceptance/record-screen-command.json`，完整日志在 `outputs/qa/r3/final/award-record-screen.log`。

## 入口二：站点真实回放与沙盒

本机打开 `http://127.0.0.1:8081/report.html#assets` 录制真实 GLB 的旋转，再打开 `http://127.0.0.1:8081/levels.html` 录制原结果与赛后修订回放，`http://127.0.0.1:8081/sandbox.html` 录制轻量沙盒。也可以运行 `python ops/export_site.py --out /tmp/beforestep-recording-site`，再运行 `python -m http.server 8081 --directory /tmp/beforestep-recording-site`。负责人首页完成集成后，首屏石头录屏入口改用站点 `/`。模型与照片来源是 `evidence/web-assets/anchor.json`，每项带任务 ID 与 SHA。

有桌面/OpenGL 时可将命令的 `MUJOCO_GL=egl` 改成 `glfw` 并去掉 `--headless`，额外观察被动 MuJoCo 窗口。服务器上的无头验证不冒充 GUI 验收。实际传感器重新渲染若与原字节不一致，会保存 NEED_LUX3D 并停止；不加载密钥或自动生成，不用新生成绕过身份核验。

网页轨迹回放与轻量沙盒均有明确标注。新视频由负责人制作，当前旧 mp4 保持历史标识。完整 22 个运行的物理、观测与渲染来源使用 `evidence/video/index.json`，不要从外包代替这些公开数据。
''')
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name != 'index.json' and not any(i['path'] == str(path.relative_to(ROOT)) for i in items):
            items.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (out / 'index.json').write_text(json.dumps({'schema': 'beforestep-award-video-kit/v1', 'items': items,
        'storyboards': [90, 45], 'source_run_index': 'evidence/video/index.json',
        'generator': {'path': 'ops/build_award_materials.py', 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'number_sources': 'evidence/video/award/number-sources.json',
        'renderer': 'Project lead; the agent prepared data, scripts and subtitles only.'}, ensure_ascii=False, indent=2) + '\n')
    post = ROOT / 'docs/award-promotion.md'
    images = [i['path'] for i in items if i['path'].endswith('.png') and 'mobile' not in i['path']][:9]
    assert 6 <= len(images) <= 9
    post.write_text(f'''# 传播材料（由负责人发布）

## 小红书：技术版

机器人拍到的只是一张平面照片。Aholo Lux3D 把它变成一整块三维石头，包括相机没有看见的那一面。我们让轮腿机器人在多份真实生成的石头旁完整预演，再到独立仿真执行：实际 RGB-D → 多候选 → 冻结自检 → 逐世界预演 → 执行 → 反事实。

原批真实生成任务 {facts['original_unique_tasks']} 个、GLB {facts['original_generated_glb']} 份。原窄道 Lux 到达，但预注册场景组也发生两次想象碰撞：一块石头完全藏在视线后，一份背面假设偏短却通过正面自检。原拒绝候选反事实 {facts['original_counterfactuals']['collisions']}/{facts['original_counterfactuals']['executed']} 碰撞。

已知决定性 {len(decisive)} 场，原想象 {known_counts.get('arrived',0)} 到达、{known_counts.get('stuck',0)} 停车、{known_counts.get('collision',0)} 碰撞。样本外 {len(revised['holdouts'])} 场，原想象 {held_counts.get('arrived',0)} 到达、{held_counts.get('stuck',0)} 停车、{held_counts.get('collision',0)} 碰撞；最终 v3 修订 {held['arrived']} 到达、{held['safe_stop']} 停车、{held['collisions']} 碰撞。Lux3D 让车走到没有想象就走不到的地方，错误的背面也会让车撞上；修订消掉碰撞，同时消掉留出中的到达收益。有效，但不绝对。{gap} oldv2 F1_003 碰撞保留。

可体验： https://codezzzsleep.github.io/next-zenith-beforestep/levels.html
源码： https://github.com/codezzzsleep/next-zenith-beforestep
报告： https://codezzzsleep.github.io/next-zenith-beforestep/report.html

#Aholo黑客松
发布后至结果公布前保持公开。

## 小红书：大众版

一张照片，能不能想出整块石头？

月面机器人只能拍到石头的一面，却要从背面旁边通过。低角度太阳让背光面全黑，换位置也照不亮。Aholo Lux3D 把实际照片变成可以转动的完整石头；转到背面，那一面是它想出来的。

先转转真实生成的石头，再看机器人怎样核对照片、在每个想象世界里走完整条路。它确实到过，也真的撞过。收紧规则后，样本外的碰撞消失，到达也消失。有效，但不绝对。网页把这些失败与原轨迹一起保留，也有可以玩的关卡。

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

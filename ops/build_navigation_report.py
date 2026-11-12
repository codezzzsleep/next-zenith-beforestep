"""Generate the independent report from terminal, published experiment records."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence/learning/navigation_v1'
NAMES={'learned':'训练导航网络','rules_cached_prior':'缓存先验规则','learned_no_prior':'网络去掉先验',
       'untrained':'未训练网络','rules_optimistic':'乐观规则','rules_conservative':'保守规则'}


def main():
    result=json.loads((EVIDENCE/'result.json').read_text());stats=result['results'];training=result['training']
    def cell(split,method):
        r=stats[split].get(method)
        return '未评估' if r is None else f"{r['arrived']}/{r['episodes']}；"+' / '.join(f'{k} {v}' for k,v in r['statuses'].items())
    table='| 方法 | 新布局128 | 更密/更大128 | 首次物理8 | 初始化修复后新物理8 |\n| --- | --- | --- | --- | --- |\n'
    for method,label in NAMES.items():table+='| '+label+' | '+' | '.join(cell(s,method) for s in ['test','ood','physical','physical_start_v2'])+' |\n'
    details='| 任务组 | 方法 | 可达任务到达 | 全部任务平均路径m | 全景观察 | 被动观察 | 规划耗时s |\n| --- | --- | --- | --- | --- | --- | --- |\n'
    for split in ['test','ood','physical','physical_start_v2']:
        for method in ['learned','rules_cached_prior']:
            r=stats[split][method]
            details+=f"| {split} | {NAMES[method]} | {r['reachable_arrived']}/{r['reachable']} | {r['mean_path_length_m']:.3f} | {r['mean_panorama_looks']:.3f} | {r['mean_passive_observations']:.3f} | {r['mean_planning_wall_seconds']:.4f} |\n"
    failures=[]
    for base,split in [('heldout','test'),('heldout','ood'),('physics','physical'),('physics-start-v2','physical_start_v2')]:
        paths=sorted((EVIDENCE/base/'episodes').glob('*learned.json')) if base=='heldout' else sorted((EVIDENCE/base).glob('*-learned/result.json'))
        cfg=json.loads((ROOT/'config/training/navigation_v1.json').read_text())
        for path in paths:
            row=json.loads(path.read_text())
            if base=='heldout' and not cfg[split]['seed_start']<=row['seed']<cfg[split]['seed_start']+cfg[split]['count']:continue
            if row['status']!='arrived':failures.append(f"- {split} / {row['seed']}: {row['status']}，目标误差 {row['goal_error_m']:.3f}m；[完整结果](../{path.relative_to(ROOT)})。")
    llm=result['llm']['llm-fixed'];sources=llm['decision_sources']
    text=f'''# 随机环境中的学习导航：首次完整结果

固定训练权重后，网络在新布局中到达 **{stats['test']['learned']['arrived']}/128**，在更密/更大的分布外布局中到达
**{stats['ood']['learned']['arrived']}/128**。对应缓存先验规则为
{stats['test']['rules_cached_prior']['arrived']}/128 与 {stats['ood']['rules_cached_prior']['arrived']}/128。
网络确实参与导航方向决策，已在独立新布局中实际执行；本次结果没有证明它超过规则。
物理与二维结果分开，首次初始化失败和修复后的新任务均保留。

[逐场交互回放](../site/navigation.html) · [机器可读完整结果](../evidence/learning/navigation_v1/result.json) ·
[测试前协议](learned-navigation-protocol.md) · [全部文件SHA](../evidence/learning/navigation_v1/custody.json)

## 模型实际学习了什么

4通道CNN读取已观测占据、已知区域、缓存先验占据、先验可用区域，预测可通行风险。
神经价值迭代用训练后的风险、代价、折扣和方向偏置输出八个移动方向分数。
模型共11132个参数，运行时不调用Dijkstra教师。训练真值和测试可达性判定仅在
仿真/监督/统计模块使用，不是控制器输入。观测更新、已见障碍门卫、八邻域拓扑
及重复状态记忆仍有规则；物理对照共用原已训练v4电机网络。

CPU实际训练20轮：1024训练场景/2048观测快照，64验证场景/128快照，耗时
{training['completed_at_unix']-training['started_at_unix']:.3f}s。最低验证损失
{training['best_validation_loss']:.6f}，仅按验证损失选权重。
权重SHA：`{result['model_sha256']}`。

![实际训练与验证损失](../site/media/navigation/training.svg)

## 首次留出与对照

训练1100000–1101023、验证2100000–2100063、测试3100000–3100127、
分布外4100000–4100127、首次物理5100000–5100007、初始化修复后物理
5200000–5200007互不重叠。分布外只改变密度/尺度，不是未见岩石类别。
同一任务六种方法共用传感器、地图分辨率、观测预算和已见障碍门卫。
全部任务与可达任务均统计；不可达任务和失败没有剔除。

{table}
![二维留出到达率及95% Wilson区间](../site/media/navigation/heldout.svg)

{details}
路径均值包含未完成轨迹，因此不能直接当成功路线效率。规划耗时来自CPU实际调用，
不包含感知、云生成排队或整体仿真耗时。模型的较低规划耗时不等于端到端更快。
每场路径、观察、碰撞、终态与决策来源见完整JSON；物理接触与动作轨迹也保留。

训练网络与未训练网络的到达差异支持参数学习具有实际作用；去掉缓存先验的同网络
结果是独立消融。乐观规则在这个0.30m视线模拟中也可完成大量任务，表明此分布
不能证明Lux3D对任意导航的必要性，也不能代替冻结窄道RGB-D/Lux3D的原实验。

## 物理初始化问题与独立修复

首次8物理任务网络4到达/1超时/3翻倒，规则5到达/3翻倒，全部保留。
三场两方法均在初始化后立即数值不稳定。v1环境先在默认(0,0)构造并稳定化，
随后才移动到随机起点；默认位置与边界墙重叠。
[初始化诊断](../evidence/learning/navigation_v1/physics-start-diagnostic.json)确认
同一场重置后的倾角104.0717°，构造前设置原起点后为0.09444°。
诊断没有计作测试成绩；[首次警告](../evidence/learning/navigation_v1/history/MUJOCO-initialization-first.txt)保留。

独立 `navigation_physics_start_v2` 仅在构造前声明原起点，并把heightfield输出放入
本次目录；原v1代码与结果保持。验证2100063两方法均到达，109单测通过后
先提交预注册621c975，再运行新8种子。两批物理结果分列。
新实验的物理岩石是扫描俯视凸包的挤出体，传感器仍为二维视线/阴影；
它验证轮腿动作、到达与接触，不是生产RGB-D和新照片Lux3D实时闭环的验收。

## 真实大语言模型接入

参考[Agentic Observer](https://github.com/codezzzsleep/gosim26-agentic-observer)的数值证据加模型判断，
本项目独立实现结构化动作候选。数值规划计算距离、可见性、缓存先验阻塞和访问次数，
模型选择候选、观察或停车；回复校验候选身份，模型间隔与错误回退明确单列。
参考项目的数值曝光规划与本项目导航任务不同，没有复用其比赛得分作本项目证据。

实调用模型 `{llm['model']}`。首次8场25请求全HTTP403/1010，8/8到达均由规则回退，
不是LLM成功。只读连接诊断定位为默认Python User-Agent被服务拒绝。
兼容请求头后，在独立6100008–6100009两场新增{llm['requests']}请求：
{llm['call_statuses'].get('ok',0)}有效回复、{llm['call_statuses'].get('failed',0)}解析失败。
实际移动来源为LLM {sources.get('llm',0)}步、咨询间隔图规划
{sources.get('graph_search_between_llm_consults',0)}步、错误回退
{sources.get('graph_search_llm_unavailable',0)}步。两方法均2/2到达，路径相同；
平均规划耗时规则{llm['outcomes']['rules_cached_prior']['mean_planning_wall_seconds']:.3f}s，
混合LLM {llm['outcomes']['rules_llm']['mean_planning_wall_seconds']:.3f}s。
该小样本验证了真实接入与动作记录，没有显示成功率改善。

累计{result['total_llm_requests']}/32请求，旧失败身份计入总预算。请求发送前落盘；
不能换目录重置计数或重发已知身份。所有请求上下文、有效回复、用量和错误保留，
私有配置与凭证不进入仓库。真实Lux新增任务为0；缓存形状迁移不写成新云生成。

## 逐场网络失败

{chr(10).join(failures)}

其他方法全部逐场结果在heldout/episodes和physics目录，未经筛选；上述清单只方便查看网络失败。

## 运行与复现

```bash
python3 -m venv .venv-nav
.venv-nav/bin/pip install -r requirements.txt -r requirements-navigation.txt

# 任意新种子；输出场景和可编译的MuJoCo配置，不调用云生成。
PYTHONPATH=src MUJOCO_GL=egl .venv-nav/bin/python ops/learned_navigation.py generate \\
  --seed 7200123 --distribution ood --mujoco --out outputs/navigation-new-world

# 发布的固定权重，重跑二维同种子对照；新目录保留独立运行身份。
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py evaluate \\
  --training assets/models/navigation_v1 --out outputs/navigation-reproduction

# 初始化修复后的物理对照，原8场失败证据仍保留。
PYTHONPATH=src MUJOCO_GL=egl .venv-nav/bin/python ops/navigation_physics_start_v2.py \\
  --training assets/models/navigation_v1 --out outputs/navigation-physics-reproduction

# 从头实际训练；已有输出仅用--resume续训，不能覆盖。
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py train \\
  --out outputs/learning/navigation-new
```

下载[导航权重](../assets/models/navigation_v1/best.pt)、
[未训练对照](../assets/models/navigation_v1/untrained.pt)、
[原训练数据](../evidence/learning/navigation_v1/training/data.npz)、
[训练来源与SHA](../evidence/learning/navigation_v1/training/identity.json)。
训练快照由种子和形状库可复现，最新优化器/随机状态检查点也保留。
`evaluate`与物理入口支持`--resume`，要求权重、参数和源码身份相同，跳过完整回合。
完整冻结生产系统与新实验分别运行；新接口不修改54个原src文件。
'''
    (ROOT/'docs/learned-navigation.md').write_text(text)
    print(ROOT/'docs/learned-navigation.md')


if __name__=='__main__':main()

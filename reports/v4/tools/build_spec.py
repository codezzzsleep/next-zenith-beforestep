"""Compose spec.json for 先见一步 项目报告书 v4.

Every number below comes from the v3 report or from records kept in the public repository
(paths are listed in SOURCES.md). The script only arranges them; it computes nothing."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://codezzzsleep.github.io/next-zenith-beforestep/'
REPO = 'https://github.com/codezzzsleep/next-zenith-beforestep'
RAW = 'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/'


def img(name, caption='', height=None, fit='contain'):
    b = {'type': 'image', 'src': f'assets/{name}', 'caption': caption, 'fit': fit}
    if height:
        b['height'] = height
    return b


def colw(ratios, i, total=180.0, gap=4.0):
    """Width in mm of column i in a row with the given ratios."""
    return (total - gap * (len(ratios) - 1)) * ratios[i] / sum(ratios)


def fit(name, width_mm):
    """Height in mm that shows the whole image at this width (no bars, no crop)."""
    path = ROOT / 'assets' / name
    if name.endswith('.svg'):
        w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', path.read_text(encoding='utf-8')).groups())
    else:
        from PIL import Image
        w, h = Image.open(path).size
    return round(width_mm * h / w, 1)


def P(text, **kw):
    return dict({'type': 'p', 'text': text}, **kw)


def H(text):
    return {'type': 'heading', 'text': text}


def callout(text, variant='note', label=None, **kw):
    b = dict({'type': 'callout', 'text': text, 'variant': variant}, **kw)
    if label:
        b['label'] = label
    return b


def row(items, ratios=None):
    b = {'type': 'row', 'items': items}
    if ratios:
        b['ratios'] = ratios
    return b


def stack(*blocks):
    return {'type': 'stack', 'blocks': list(blocks)}


def card(title=None, text=None, variant='default', blocks=None):
    b = {'type': 'card', 'variant': variant}
    if title:
        b['title'] = title
    if text:
        b['text'] = text
    if blocks:
        b['blocks'] = blocks
    return b


facts = [
    {'id': 'lux_created', 'display': '491', 'context': 'Lux3D 生成任务真实创建次数（全项目累计）', 'source': 'evidence/production-v6/facts.json /lux/live_ledger_counts/created', 'status': 'observed'},
    {'id': 'lux_glb', 'display': '460', 'context': '拿回的 3D 模型份数；其余 31 次为服务端生成失败', 'source': 'evidence/production-v6/facts.json /lux/live_ledger_counts/statuses', 'status': 'observed'},
    {'id': 'gallery_models', 'display': '306', 'context': '模型陈列室里可用官方 Aholo Viewer 查看的模型数；其中 110 份通过检查、196 份被拦下', 'source': 'site/data/gallery.json /stats', 'status': 'observed'},
    {'id': 'r1_arrive', 'display': '113 秒', 'context': 'R1 窄道，Lux3D 想象 + 预演，仿真时钟 112.84 秒到达，只看一眼', 'source': 'evidence/production-v6/facts.json /r1/imagination', 'status': 'observed'},
    {'id': 'r1_crash', 'display': '80 秒', 'context': 'R1 窄道，直接走，仿真时钟 80.87 秒碰撞', 'source': 'evidence/production-v6/facts.json /r1/optimistic', 'status': 'observed'},
    {'id': 'wheel_fail', 'display': '0 / 90', 'context': '10–15 厘米门槛石上只靠轮子的通过次数', 'source': 'evidence/production-v6/facts.json /legs', 'status': 'observed'},
    {'id': 'leg_pass', 'display': '24 / 24', 'context': '同一高度范围逐个抬轮的干净通过次数', 'source': 'evidence/production-v6/facts.json /legs', 'status': 'observed'},
    {'id': 'hard_scenes', 'display': '3 / 8', 'context': '8 个难场景里想象到达的场景数；另 3 停 2 撞', 'source': 'evidence/production-v6/facts.json /decisive_eight', 'status': 'observed'},
    {'id': 'forced', 'display': '17 / 102', 'context': '强行相信被拦下的想象，102 次里 17 次撞上', 'source': 'evidence/suite/summary.json /counterfactuals', 'status': 'observed'},
    {'id': 'back_short', 'display': '23 / 64', 'context': '通过检查的 64 份想象里，背面比真石头短 5 厘米以上的份数', 'source': 'evidence/production-v6/facts.json /back_error', 'status': 'observed'},
    {'id': 'mission_worlds', 'display': '12 / 12', 'context': '可玩任务里 12 个模型世界的完整预演全部通过', 'source': 'docs/mission-verification.json /worlds', 'status': 'observed'},
    {'id': 'mission_finish', 'display': '174 秒', 'context': '可玩任务验证：仿真时钟 174.26 秒停稳，距终点中心 0.10 米', 'source': 'docs/mission-verification.json /finish', 'status': 'observed'},
    {'id': 'mission_crash', 'display': '56 秒', 'context': '同一任务里只信看得见那一面的路线，56.34 秒碰上高石头', 'source': 'docs/mission-verification.json /optimistic', 'status': 'observed'},
]

pages = []

# ---------------------------------------------------------------- 01 core
pages.append({
    'id': 'core', 'kicker': '01 · LUX3D 在作品里做什么', 'title': '一张照片，换回一整块石头',
    'lead': '核心只有一个动作：把机器人拍到的一张石头照片交给 Lux3D，拿回一整块石头的 3D 模型。后面所有判断都建立在这个模型上。',
    'blocks': [
        row([
            img('photo-5958685.jpg', '**机器人拍到的照片**\n只有石头朝向自己的这一面。', 46),
            img('viewer-front.jpg', '**Lux3D 交回的模型**\n同一个真实任务，任务号 5958685。', 46),
            img('viewer-back.jpg', '**转到背面**\n照片上没有的那一面，现在有了形状。', 46),
        ], [1, 1.366, 1.366]),
        {'type': 'metrics', 'fact_ids': ['lux_created', 'lux_glb', 'gallery_models'], 'items': [
            {'value': '491', 'unit': '次', 'label': '真实调用 Lux3D', 'note': '每次都留下任务号、输入照片和结果'},
            {'value': '460', 'unit': '份', 'label': '拿回的 3D 模型', 'note': '另有 31 次服务端没有生成成功'},
            {'value': '306', 'unit': '份', 'label': '在网页里亲手转着看', 'note': '用官方 Aholo Viewer 直接打开原始模型'},
        ]},
        img('model-wall.jpg', '**网页陈列室里的全部 306 份 Lux3D 模型，每一格是一次真实调用交回的石头。**底边绿色的 110 份通过了检查，橙色的 196 份被拦下；被拦下的也原样保留，可以打开看它错在哪。', fit('model-wall.jpg', 180)),
        H('模型拿回来以后，判断都建立在它上面'),
        {'type': 'cards', 'cols': 3, 'items': [
            {'title': '核对', 'text': '把模型放回相机看到的位置，和看得见的那一面比一遍，对不上的丢掉。', 'variant': 'top'},
            {'title': '预演', 'text': '每份通过的模型各搭一个虚拟世界，让机器人在里面把整条路先走一遍。', 'variant': 'top'},
            {'title': '行动', 'text': '所有世界都走得通才出发；有一个会撞，就再看一眼，或者停下。', 'variant': 'top'},
        ]},
    ]})

# ---------------------------------------------------------------- 02 advantage
pages.append({
    'id': 'advantage', 'kicker': '02 · 它带来的优势', 'title': '同一条月面路，三种结局',
    'lead': '月面上挡路的石头有两种：高石头绕得过去，但背面看不见；门槛石看得清楚，但轮子滚不上去。两种石头放在同一条路上，同一台机器人、同一个起点，只换它手里有什么。',
    'blocks': [
        img('lanes.svg', '示意图：按先后画出三次运行各停在哪里，距离不按比例。数字来自可玩任务的独立物理验证记录：12 / 12 个模型世界预演通过，81 秒绕到门槛前；从门槛前只靠轮子行驶 60 秒没能过线；逐腿跨过后 174 秒停进终点圈。', fit('lanes.svg', 180),
            ) | {'fact_ids': ['mission_crash', 'mission_worlds', 'mission_finish']},
        row([
        img('showcase-model.jpg', '**Lux3D 管高石头。**停在观察点，转看原模型的背面，再选择脑内试路或带着 3D 参考驾驶。模型实际参与核对与碰撞预演。', fit('showcase-model.jpg', 88)),
        img('showcase-leg.jpg', '**腿管门槛石。**相机量出门槛高 11.9 厘米，轮子滚不上去；玩家逐腿触发抬、移、落，控制器辅助稳住重心和支撑。', fit('showcase-leg.jpg', 88)),
        ]),
        callout('Lux3D 让机器人**敢绕高石头，并且绕得对**；腿让它**跨得过轮子过不去的门槛**。少了前者，车撞在第一种石头上；少了后者，车停在第二种石头前。两样合在一台轮腿机器人上，这条路才走得完。', 'good', '这就是我们想说的优势'),
        callout('对照来自作品里的可玩任务（第 7 页），全部是 MuJoCo 仿真。高石头沿用 R1 场景和 11 份真实 Lux3D 模型；门槛石由相机直接测量，没有经过 Lux3D。这条路是为展示搭的，不在预先固定的实验场景之内，结论只对应这条路线和这批模型。多场景的统计、撞车和停车的案例在第 8 到 10 页。', 'warn', '口径'),
    ]})

# ---------------------------------------------------------------- 03 problem
pages.append({
    'id': 'problem', 'kicker': '03 · 问题', 'title': '机器人为什么会“进退两难”？',
    'lead': '因为它只看得见石头朝向自己的一面。同一条路、同一个机器人，我们让它用三种办法对待“看不见的那部分”。',
    'blocks': [
        {'type': 'gallery', 'cols': 3, 'fact_ids': ['r1_crash', 'r1_arrive'], 'items': [
            {'src': 'assets/way-crash.jpg', 'height': 32.2, 'caption': '[[r:撞上了]] **办法一：当它不存在**\n看不见就当没有，直接走。80 秒后撞上石头。'},
            {'src': 'assets/way-stop.jpg', 'height': 32.2, 'caption': '[[a:不敢走]] **办法二：当它很危险**\n看不见的都当障碍，看了 5 次也找不到路，停下。'},
            {'src': 'assets/way-arrive.jpg', 'height': 32.2, 'caption': '[[g:到达]] **办法三：让 Lux3D 想象**\n只看一眼，先想象背面再走，113 秒到达终点。'},
        ]},
        callout('光靠“敢不敢”解决不了问题，机器人需要一个有依据的猜测。Lux3D 提供的就是这个猜测：一整块石头的 3D 形状。', 'good'),
        row([
            stack(
                H('为什么月球上尤其难'),
                card('黑影里没有深度', '月球南极太阳贴着地平线，每块石头拖着长长的黑影，相机在黑影里测不到有用的距离。'),
                card('石头自己会挡人', '前面的石头挡住身后的区域，机器人走近之前，根本不知道后面有什么。'),
                card('走错一步代价很大', '月面上没有人能过去扶一把。撞上石头或者卡住，任务可能就此结束，所以迈步之前必须想清楚。'),
            ),
            img('first-look.jpg', '**机器人的“第一眼”。**它能看见石头朝向自己的这一面，背面一片空白。', fit('first-look.jpg', colw([1, 1.12], 1))),
        ], [1, 1.12]),
        H('我们怎么验证'),
        P('在 MuJoCo 物理仿真搭起来的月球南极环境里，放进真实扫描的月面石头，太阳只高出地平线几度，一台带腿的轮式机器人。让机器人把 Lux3D 生成的 3D 模型当作石头背面的“想象”，用它判断、走路，看结果。'),
    ]})

# ---------------------------------------------------------------- 04 method
pages.append({
    'id': 'method', 'kicker': '04 · 办法', 'title': '让想象先过四关，再迈步',
    'lead': '拿到 Lux3D 的 3D 模型之后，机器人不会直接相信它。',
    'blocks': [
        {'type': 'process', 'key': 3, 'items': [
            {'title': '拍照，想象', 'text': '照片交给 Lux3D，同一块石头生成 5 到 6 份不同的模型'},
            {'title': '对一遍', 'text': '和相机看到的那一面对照，对不上的丢掉'},
            {'title': '各走一遍', 'text': '每份想象放进一个虚拟世界，把整条路走完'},
            {'title': '全安全才迈步', 'text': '有一份会撞车就不出发，宁可停下'},
        ]},
        img('six-candidates.jpg', '**第 1 步：**同一眼拍到的石头 A，按三种裁法各交给 Lux3D 两次，拿回六份整块石头。背面各不相同，所以机器人不押其中一份。', fit('six-candidates.jpg', 180)),
        row([
            img('twelve-worlds.jpg', '**第 3 步：**十二个“想象世界”同时让机器人把同一条路走一遍，每一格是一份想象的组合。', fit('twelve-worlds.jpg', colw([1.22, 1], 0))),
            stack(
                callout('Lux3D 的输出在这里是“假设”，不是“答案”：它给了机器人一个可以检验的东西，也可能出错，所以必须被检验。', 'dark', '设计立场'),
                {'type': 'list', 'variant': 'check', 'items': [
                    '**3D 模型：**一张照片换回一整块石头，背面也有形状',
                    '**多份候选：**同一块石头生成多份，背面各不相同，不押一份',
                    '**可旋转查看：**用 Aholo Viewer 在网页里转到背面',
                ]},
            ),
        ], [1.22, 1]),
        H('R1 场景里，四关是怎么一步步筛的'),
        {'type': 'table', 'variant': 'dark', 'columns': ['步骤', '石头 A', '石头 B'], 'rows': [
            ['Lux3D 生成', '6 份', '6 份，1 份服务端失败，剩 5 份'],
            ['和相机看到的那一面对一遍', '6 份全部通过', '5 份里通过 2 份'],
            ['12 个想象世界里把路走一遍', '全部没有撞车，机器人才出发，最后到达终点', '同左'],
        ]},
    ]})

# ---------------------------------------------------------------- 05 legs
pages.append({
    'id': 'legs', 'kicker': '05 · 轮腿', 'title': '有些石头不需要想象，需要的是腿',
    'lead': '路上除了高大的石头，还有十几厘米高的门槛石。相机站得高，看得清清楚楚，但轮子滚不上去。',
    'blocks': [
        row([
            stack(img('wheel-stuck.jpg', '', fit('wheel-stuck.jpg', 88)),
                  {'type': 'ratio', 'value': 0, 'total': 90, 'label': '只靠轮子', 'fact_ids': ['wheel_fail'],
                   'note': '顶在门槛石前过不去。在 10 到 15 厘米高的门槛石上试了 90 次，一次都没成功。'}),
            stack(img('leg-lift.jpg', '', fit('leg-lift.jpg', 88)),
                  {'type': 'ratio', 'value': 24, 'total': 24, 'label': '把轮子逐个抬起来', 'fact_ids': ['leg_pass'],
                   'note': '轮子装在腿上，可以一个一个迈过去。试了 24 次，全部干净通过。'}),
        ]),
        card('我们修正了自己最初的想法',
             '一开始我们以为，腿跨石头也需要 Lux3D 补出完整形状。实测后发现不是：矮石头相机看得全，只用看到的形状，机器人就能抬腿跨过去。在这种石头上前后用 Lux3D 生成了 53 次，只有 7 份通过检查；在一个开发场景里，通过检查的想象把石头想成约 19 厘米深（真实 11 到 13 厘米），超出腿能跨的 15 厘米，用想象的车停在了门前，而只信看得见形状的车 191 秒干净跨过。'),
        callout('想象解决“看不见背面的高石头”，腿解决“看得见但轮子过不去的矮石头”，各解决一种。', 'good', '结论'),
        row([
            img('route-check.jpg', '', fit('route-check.jpg', colw([1.3, 1], 0))),
            stack(H('两种石头放在同一条路上'),
                  P('先绕过高石头，再抬腿跨过门槛石，到达终点。'),
                  P('这是用真实形状做的路线检查，说明这条路走得通；不是想象的结果。换成 Lux3D 的想象来决定怎么走，结果在第 3 页和第 10 页。')),
        ], [1.3, 1]),
    ]})

# ---------------------------------------------------------------- 06 mission
pages.append({
    'id': 'mission', 'kicker': '06 · 亲手试', 'title': '这条路，你可以自己开一遍',
    'lead': '打开网页就能驾驶：先到高石前停车，转看 Lux3D 的完整模型，再试路或带着 3D 参考自己开；绕过高石、逐腿跨过门槛，驶入终点。浏览器实时计算物理，不用安装。',
    'blocks': [
        {'type': 'gallery', 'cols': 2, 'items': [
            {'src': 'assets/showcase-model.jpg', 'height': 48.4, 'caption': '**先看另一面。**高石前自动制动、打开模型气泡。实际转看原 GLB 后，选择脑内试路或手动驾驶。'},
            {'src': 'assets/showcase-manual.jpg', 'height': 48.4, 'caption': '**自己开也有 3D。**行驶时真实模型继续在小气泡中旋转；经过第二块高石，提示换一份假设。'},
            {'src': 'assets/showcase-leg.jpg', 'height': 48.4, 'caption': '**轮子变成脚。**1–4 选腿，J 抬起、K 前移、L 落地。图取自已有完整录像，控制器辅助支撑。'},
            {'src': 'assets/showcase-finish.jpg', 'height': 48.4, 'caption': '**完成整条路。**新版实录完成四腿 12 个主要动作、两模型世界预演，并驶入终点圈。'},
        ]},
        row([
            stack(H('怎么操作'),
                  P('**轮行：**W A S D 或方向键，手机用摇杆；空格刹车。'),
                  P('**迈腿：**1–4 选右前、左前、右后、左后腿；J 抬起、K 前移、L 落地。'),
                  P('**看与试：**Q 展开模型；V 切第一/第三/俯视；画中画看同一时刻。')),
            stack(H('它是真的在算'),
                  P('11 份真实候选里 8 份通过核对，所选 GLB 参与碰撞计算。默认两世界，最多 12 个；全部实际预演通过后，才能按该路线辅助行驶。手控可接管。'),
                  P('16 个电机驱动物理；四种视图对应同一真实状态。')),
        ]),
        callout('复用已有真实 Lux3D 模型，不提交当前相机图。看完模型只释放手控；辅助行驶还须从当前停稳状态实际通过所选世界的预演，改候选即失效。除重置与独立预演起点外不直接摆机器人位置。新版连续实录 5 分 33 秒在 `evidence/showcase-guided-20261116/`；旧键盘片仍保留。游玩成绩与第 8 到 10 页实验分开。', 'warn', '边界'),
    ]})

# ---------------------------------------------------------------- 07 trust
pages.append({
    'id': 'trust', 'kicker': '07 · 可信度', 'title': '想象出来的背面，靠谱吗？',
    'lead': '我们把 Lux3D 想象的石头，和模拟器里石头真正的样子逐份对比。结论：**能用，但不能全信。**',
    'blocks': [
        H('检查，真的拦住了不靠谱的'),
        row([
            img('chart-iou.svg', '石头 B 的 5 份想象，和相机看到的那一面的吻合度。及格线在看到任何候选之前固定；5 份里 3 份被拦下。', fit('chart-iou.svg', colw([1.15, 1], 0))),
            {'type': 'metric', 'variant': 'vertical', 'value': '17 / 102', 'label': '强行相信被拦下的想象', 'fact_ids': ['forced'],
             'note': '把被拦下的想象强行“相信”一遍再走：在 12 个预先固定的月面场景里试了 102 次，17 次让车撞上石头，大约每 6 次 1 次。说明这道检查确实拦下了会出事的想象。'},
        ], [1.15, 1]),
        H('但检查不是万能的'),
        row([
            {'type': 'metric', 'variant': 'vertical', 'value': '23 / 64', 'label': '通过了检查，背面仍然偏短', 'fact_ids': ['back_short'],
             'note': '通过检查的 64 份想象里，23 份背面比真实石头短了 5 厘米以上，超过三分之一。'},
            stack(
                img('chart-gap.svg', '到达终点的那次运行（R1），车和两块石头的全程最小间隙，按实际碰撞几何复盘；执行中没有接触。', fit('chart-gap.svg', colw([1, 1.15], 1))),
                callout('车和石头最近只差约 4.8 厘米。路是险险走过去的。', 'warn'),
            ),
        ], [1, 1.15]),
        callout('Lux3D 的想象足够有用，能让机器人走通原本走不通的路；但它会出错，每一份都必须被检验、被预演。这就是“先见一步”：先在想象里走一步，再迈真正的一步。', 'good', '所以'),
    ]})

# ---------------------------------------------------------------- 08 scenes
pages.append({
    'id': 'scenes', 'kicker': '08 · 多场景', 'title': '换很多场景，这套办法还有用吗？',
    'lead': '只在一个场景成功说明不了问题，所以我们在看到任何结果之前，先固定了 12 个月面场景，之后不换、不挑。',
    'blocks': [
        card('怎么挑出“最难的”场景',
             '先让别的办法跑一遍：只要直接走会撞、保守走不通、而把石头真实形状告诉机器人就能到达，这个场景就说明路是通的，难点正是看不见的背面。这样的场景一共 8 个，我们专门拿它们检验想象有没有用。', 'dark'),
        H('这 8 个场景里，三种办法的结果'),
        img('chart-eight.svg', '前两行是对照组，0 次到达由挑场景的方式决定；要看第三行：想象让 8 个场景里的 3 个变得可以走通，另有 3 次停车、2 次撞车。', fit('chart-eight.svg', 180)),
        {'type': 'metric', 'value': '3 / 8', 'label': '想象走通的场景', 'fact_ids': ['hard_scenes'],
         'note': '别的办法一个都到不了的场景里，想象带机器人走通了 3 个。另一条参考：假设相机在黑影里也能测深度（月面上做不到），这个办法在 8 个场景里能到 5 个，只作为“理想情况能到哪”的上限。'},
        H('想象撞车的那两次'),
        row([
            img('crash-short-back.jpg', '[[r:撞车]] **背面想短了。**这份想象的正面和相机看到的完全吻合，通过了检查，但背面比真石头短，机器人以为那里没有石头。', fit('crash-short-back.jpg', colw([1.1, 1], 0))),
            stack(
                card('另一次', '有一块石头藏在大石头后面，机器人从没见过它，自然没有为它生成想象，也就没有检验。'),
                callout('想象能弥补“看不见”，前提是机器人至少知道那里有东西。这是接下来要改进的地方。', 'dark'),
            ),
        ], [1.1, 1]),
    ]})

# ---------------------------------------------------------------- 09 boundary
pages.append({
    'id': 'boundary', 'kicker': '09 · 边界', 'title': '它的边界在哪里？',
    'lead': '把两种石头放在同一条路上，换成 Lux3D 的想象来决定怎么走，一共 5 个场景。',
    'blocks': [
        {'type': 'cards', 'cols': 2, 'items': [
            {'title': '场景 1、2：高石头不难', 'variant': 'top',
             'text': '[[g:有腿：到达]] 绕过高石头，抬腿跨过门槛石。\n[[r:没有腿：卡住]] 到门槛石前过不去。\n说明腿是必须的。只信看得见形状的那辆车也到了，所以这两条路上看不出想象的作用。'},
            {'title': '场景 3、4、5：后面还有一块被挡住的石头', 'variant': 'top',
             'text': '[[a:四辆车全部停下]] 车身没有碰到石头。\n有的场景里想象没有一份通过检查，机器人宁可停下；有的场景里通过检查的那份把背面想短了，轮子碰到石头，被安全监视器拦停。'},
        ]},
        row([
            img('scene5-stop.jpg', '**场景 5：停在高石头前。**它看了两眼，Lux3D 为后面那块石头生成的 17 份想象，没有一份通过检查，所以没有往前走。', fit('scene5-stop.jpg', colw([1.45, 1], 0))),
            callout('那块石头在第一眼照片里只有二百多像素高，能看到的信息很少。单张照片让 Lux3D 想象不出可信的形状，机器人选择停下而不是冒险。\n\n**下一步：**从多个角度拍照再生成。', 'warn', '边界'),
        ], [1.45, 1]),
        H('这 17 份想象，尺寸为什么不对'),
        row([
            img('plot-17-sizes.jpg', '', fit('plot-17-sizes.jpg', colw([2.3, 1], 0))),
            stack(P('每个点是一份想象，纵轴是想象的石头除以真实石头的大小。'),
                  P('多数只有真实的六成多到八成多，个别又偏大，都落在绿色可信范围（0.89 到 1.09）之外。')),
        ], [2.3, 1]),
        callout('第 3 页那条路上，高石头是 R1 场景里 Lux3D 想象得准的那一类，所以想象和腿接得上。这一页说明：当石头在照片里太小、被挡得太多时，想象通不过检查，机器人会停下。优势成立的前提，是照片里看得到足够多的石头。', 'note', '和第 3 页的关系'),
    ]})

# ---------------------------------------------------------------- 10 process
pages.append({
    'id': 'process', 'kicker': '10 · 过程', 'title': '从一个想法，到一遍遍被推翻',
    'lead': '作品经历了几个节点，其中有两次是我们自己推翻了自己。',
    'blocks': [
        {'type': 'timeline', 'caption': '按先后排列，节点等距，不表示时间间隔。橙色节点是被我们自己推翻的想法。', 'items': [
            {'date': '起点', 'title': '最初的想法', 'text': '把真实观测和 Lux3D 的生成结果融合起来。发现融合时会把没看见的地方误填成实心，修掉了这个缺陷。'},
            {'date': '对照', 'title': '窄道实验', 'text': '一条窄道上，直接走、保守、想象三种办法同场对比：想象一次到达，另外两种一撞一停。这是后面所有工作的起点。'},
            {'date': '扩大', 'title': '12 个场景', 'text': '提前固定 12 个场景、不换不挑。12 个场景里想象撞了 2 次，后来补充的 5 个留出场景里又撞了 2 次，共 4 次，每一次都查清了原因。'},
            {'date': '收紧', 'title': '收紧规则', 'text': '看过结果后加了一条规则：想象只解释“太阳黑影”，被挡住的部分仍当作危险。再跑 17 个场景，没有撞车，但机器人更常停下。这是看过结果后改的规则，结果只作参考。'},
            {'date': '推翻自己 ①', 'title': '腿不需要完整 3D', 'status': 'failed', 'text': '原以为腿跨石头也需要完整 3D，实测推翻：矮石头相机看得全，Lux3D 反而添乱。于是把“想象”和“腿”分成两种石头来讲。'},
            {'date': '推翻自己 ②', 'title': '不是“缺一不可”', 'status': 'failed', 'text': '同一条路上放两种石头，原以为想象和腿缺一不可。5 个场景跑完，没有一个场景同时支持这个说法，于是我们把结论收窄成各解决一种石头。'},
            {'date': '现在', 'title': '接成一个可以亲手开的任务', 'text': '把 R1 的高石头和一段看得见的门槛接在同一条路上，做成网页里能亲手开的月面任务，并留下独立的物理验证记录（第 3、7 页）。'},
        ]},
        row([
            card('做这件事用到的工具', '**Aholo Lux3D** 生成模型，**Aholo Viewer** 在网页里展示，**MuJoCo** 计算物理。代码用 Python 和浏览器端 JavaScript 编写，开发过程中使用了 AI 编程助手，所有实验记录、任务号和失败案例都留在仓库里。', 'white'),
            card('我们坚持的做法', '先定规则再看结果；看过结果才改的规则单独标明，只作参考；撞车、停车和被推翻的想法都写进报告，不挑着讲。', 'white'),
        ]),
    ]})

# ---------------------------------------------------------------- 11 assets
pages.append({
    'id': 'assets', 'kicker': '11 · 关键资产', 'title': '真实的 3D 模型长什么样',
    'lead': '项目不同阶段留下的真实模型与输入图，都是浏览器里真实渲染的截图。每个版本的源码、输入图和生成结果都保存在仓库里。',
    'blocks': [
        row([
            img('six-versions.jpg', '', fit('six-versions.jpg', colw([1.3, 1], 0))),
            stack(H('六个版本'),
                  P('每一格上面是当时的模型，下面是对应的输入图。'),
                  P('V6、V7、V8 是早期版本；v0.1 到 v0.3 是后期三次实验，其中 v0.1 和 v0.3 展示的候选被检查拒绝，v0.2 展示的候选通过。')),
        ], [1.3, 1]),
        H('同一块门槛石，换 6 种输入图'),
        row([
            stack(
                {'type': 'metrics', 'cols': 2, 'items': [
                    {'value': '0 / 29', 'label': '前 5 种输入图', 'note': '29 份全部被拦'},
                    {'value': '7 / 24', 'label': '第 6 种输入图', 'note': '24 份里通过 7 份'},
                ]},
                P('前 5 种结果多数高度是真实石头的 1.6 倍左右；第 6 种换成带月面地面和阴影的真实场景截图。喂给 Lux3D 的图什么样，会明显影响生成结果。'),
            ),
            img('input-rounds.jpg', '第 5 轮（上，被拒）和第 6 轮（下，通过）。', fit('input-rounds.jpg', 88)),
        ]),
        H('石头 B：第一眼被挡，机器人走了一步再补看'),
        row([
            img('rock-b-relook.jpg', '', fit('rock-b-relook.jpg', 88)),
            card('怎么补看', '同一块石头的两次输入和 Lux3D 生成的模型。第一眼被前面的石头挡住大半，机器人往前走到新位置再拍一次。这个例子里两次生成都没有通过检查，所以机器人没有硬走。'),
        ]),
    ]})

# ---------------------------------------------------------------- 12 stack
pages.append({
    'id': 'stack', 'kicker': '12 · 技术栈', 'title': '群核的技术，用在了哪里',
    'lead': '作品里真实调用 Lux3D 四百多次，并用官方 Aholo Viewer 在网页里展示这些模型。',
    'blocks': [
        {'type': 'table', 'variant': 'dark', 'columns': ['技术', '在作品里做什么', '用了多少', '在哪里能看到'], 'rows': [
            ['**Aholo Lux3D**', '核心。把机器人拍到的照片生成整块石头的 3D 模型，模型进入核对、预演和行动', '491 次真实调用，拿回 460 份模型', '任务号与输入图逐条记录在仓库'],
            ['**Aholo Viewer**', '在网页里旋转查看 Lux3D 返回的原始模型，转到背面', '首页、模型陈列室、月面任务三处', '陈列室可看全部 306 份'],
            ['**MuJoCo**', '物理仿真。机器人的所有运动、碰撞都由它计算；网页版在浏览器里实时运行', '全部实验与月面任务', '实验回放与月面任务'],
        ]},
        H('一次 Lux3D 调用，从照片到判断'),
        {'type': 'process', 'items': [
            {'title': '机器人拍照', 'text': '从它当时的位置截下石头朝向自己的那一面'},
            {'title': '交给 Lux3D', 'text': '上传照片，创建生成任务，记下任务号'},
            {'title': '拿回模型', 'text': '下载整块石头的模型，原件按任务号存档'},
            {'title': '放回现场', 'text': '对齐到相机看到的位置，进入核对和预演'},
        ]},
        {'type': 'cards', 'cols': 3, 'items': [
            {'title': '为什么要调用四百多次', 'variant': 'top', 'text': '同一块石头每次生成 5 到 6 份；十几个场景、两种石头、补看和换输入图都是真实调用，没有一份模型是手工做的或事先挑好的。'},
            {'title': '失败的也算数', 'variant': 'top', 'text': '被检查拦下的模型、服务端没生成成功的任务，都留在记录里。陈列室里“被拒模型”“信了会撞”可以单独筛出来看。'},
            {'title': '新在哪里', 'variant': 'top', 'text': '图片转 3D 通常用来做好看的资产。这里它是机器人对“看不见那一面”的假设：先检验、预演，再决定轮腿怎么走。'},
        ]},
        img('site-gallery.jpg', '**模型陈列室**（codezzzsleep.github.io/next-zenith-beforestep/gallery.html）。左边用官方 Aholo Viewer 转着看原始模型，右边是它的输入照片和当时的检查结论。', fit('site-gallery.jpg', 180)),
    ]})

# ---------------------------------------------------------------- 13 links
defs = [
    {'term': '想象', 'text': 'Lux3D 根据照片生成的整块石头的 3D 模型，被当作对“背面”的假设。'},
    {'term': '通过检查', 'text': '想象的模型和相机看到的那一面足够吻合，才有资格被机器人使用。'},
    {'term': '预演', 'text': '在虚拟世界里让机器人把整条路走一遍，但并不真的出发。'},
    {'term': '难场景', 'text': '直接走会撞、保守走不通、但真实形状能走通的场景，一共 8 个。'},
    {'term': '门槛石', 'text': '十几厘米高的矮石头，机器人看得清楚，轮子滚不上去。'},
    {'term': '轮腿', 'text': '四条腿、每条腿末端一个驱动轮：平地用轮子走，遇到门槛把轮子逐个抬过去。'},
    {'term': '到达', 'text': '走到终点。'},
    {'term': '停车', 'text': '因为不安全或找不到路而停下。'},
    {'term': '撞车', 'text': '车身碰到了石头。'},
]
pages.append({
    'id': 'links', 'kicker': '13 · 入口与复现', 'title': '你可以自己去看、自己去跑',
    'blocks': [
        row([
            {'type': 'link', 'label': '在线作品', 'url': SITE, 'description': '首页直接看照片和模型，旋转到背面；含 185 秒完整 Demo。'},
            {'type': 'link', 'label': '月面任务（可玩）', 'url': SITE + 'play.html', 'description': '键盘或手机摇杆，亲手绕行、迈腿、抵达。'},
        ]),
        row([
            {'type': 'link', 'label': '模型陈列室', 'url': SITE + 'gallery.html', 'description': '306 份 Lux3D 模型，官方 Aholo Viewer 旋转查看。'},
            {'type': 'link', 'label': '实验回放', 'url': SITE + 'levels.html', 'description': '各场景三种办法的原始运行回放，成功和失败都在。'},
        ]),
        row([
            {'type': 'link', 'label': 'Demo 视频', 'url': REPO + '/tree/main/evidence/lux3d-demo-v2', 'description': '2 分 37 秒，中文配音与字幕，全部为仿真实录。'},
            {'type': 'link', 'label': '源代码与全部记录', 'url': REPO, 'description': '491 个 Lux3D 任务号、输入图与全部实验记录。'},
        ]),
        card('一条命令复现', '克隆仓库后运行 `./setup.sh` 和 `.venv/bin/python ops/quickstart.py --reuse-lux --serve`，复用仓库里的真实 Lux3D 模型，不需要密钥，不产生新的费用。这条命令重跑的是 R1 窄道：观测、核对、12 个世界的完整预演和独立执行。', 'white'),
        H('几个术语的白话解释'),
        {'type': 'columns', 'cols': 3, 'items': [{'title': d['term'], 'text': d['text']} for d in defs[:6]]},
        P('**到达：**走到终点。**停车：**因为不安全或找不到路而停下。**撞车：**车身碰到了石头。\n本报告所有结果均来自 MuJoCo 物理仿真，不是实机，也不是现场实时生成。'),
    ]})

spec = {
    'version': 2,
    'document': {'title': '先见一步 · 项目报告书 v4', 'mode': 'compose', 'audience': 'Aholo 全球 3D AI 黑客松评审', 'allow_rewrite': True},
    'style': {'preset': 'tech-lab', 'palette': 'midnight', 'cover': 'numbers', 'header': 'kicker', 'art': 'contours',
              'radius': 'soft', 'card': 'tint', 'fontpair': 'serif-sans', 'density': 'regular', 'footer': 'rule'},
    'cover': {
        'kind': 'numbers', 'title': '先见一步', 'subtitle': 'BeforeStep · 轮腿机器人借 Lux3D 走月面',
        'kicker': 'AHOLO 全球 3D AI 黑客松 · 项目报告书 · 队伍 NEXT ZENITH',
        'description': '核心只有一个动作：把机器人拍到的一张石头照片交给 Lux3D，拿回一整块石头的 3D 模型。后面所有判断都建立在这个模型上。\n\n有了它，轮腿机器人敢绕开看不见背面的高石头；遇到轮子滚不上去的门槛石，再把轮子逐个抬过去。',
        'visual': {'src': 'assets/leg-shadow.jpg'},
        'meta': [{'label': '版本', 'value': 'v4 · 2026 年 11 月'}, {'label': '画面', 'value': '均为 MuJoCo 仿真实录'}],
        'metrics': [{'value': '1 张', 'label': '照片交给 Lux3D，换回整块石头'},
                    {'value': '491 次', 'label': '真实调用 Lux3D，次次有任务号'},
                    {'value': '12 个', 'label': '想象世界，全走通才出发'}],
    },
    'facts': facts,
    'pages': pages,
}
spec['inventory'] = 'inventory.json'
for source_id, mapping in json.loads((ROOT / 'content-map.json').read_text(encoding='utf-8')).items():
    path = mapping['target'].split('/')
    node = spec['cover'] if path[0] == 'cover' else next(p for p in pages if p['id'] == path[0])
    for key in path[1:]:
        node = node[int(key)] if isinstance(node, list) else node[key]
    node.setdefault('source_ids', []).append(source_id)
    note = mapping['rewrite_note']
    if note not in node.get('rewrite_note', ''):
        node['rewrite_note'] = (node.get('rewrite_note', '') + ' ' + note).strip()
(ROOT / 'spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('pages', len(pages))

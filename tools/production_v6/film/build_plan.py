"""Build the final-film script from verified facts and retained shots."""
from pathlib import Path
import collections
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import ROOT, OUT, sha, save, status, load_state

WORK = OUT / 'film'
facts = json.loads((OUT / 'facts.json').read_text())
assert not facts['mismatches']
index = json.loads((OUT / 'shots/index.json').read_text())
shots = {r['id']: r for r in index['shots']}
bindings = {}

def fact(path):
    x = facts
    for k in path.split('/'):
        x = x[int(k)] if isinstance(x, list) else x[k]
    assert x['status'] == 'verified', path
    assert sha(ROOT / x['source']) == x['source_sha256'], path
    bindings[path] = x
    return x['value']

def integer(n):
    n = int(n)
    if n < 10: return '零一二三四五六七八九'[n]
    if n < 20: return '十' + (integer(n % 10) if n % 10 else '')
    if n < 100: return integer(n // 10) + '十' + (integer(n % 10) if n % 10 else '')
    if n < 1000:
        rest = n % 100
        return integer(n // 100) + '百' + ('零' if 0 < rest < 10 else '') + (integer(rest) if rest else '')
    raise ValueError(n)

def decimal(n, places=2):
    a, b = f'{n:.{places}f}'.split('.')
    return integer(int(a)) + '点' + ''.join(integer(int(c)) for c in b)

O = fact('r1/optimistic/sim_time_s')
C = fact('r1/conservative/sim_time_s')
I = fact('r1/imagination/sim_time_s')
looks = fact('r1/conservative/looks')
count = fact('back_error/candidate_count')
short = fact('back_error/shorter_than_five_cm')
error = abs(fact('back_error/r1_reveal_examples/0/back_error_m'))
short_threshold_cm = round(abs(fact('back_error/threshold_m')) * 100)
decisive = fact('decisive_eight/count')
arrived = fact('decisive_eight/imagination/counts/arrived')
collisions = fact('decisive_eight/imagination/counts/collision')
stopped = fact('decisive_eight/imagination/counts/safe_stop')
post_count = fact('post_result_v3/completed')
post_collisions = fact('post_result_v3/collisions')
post_stop = fact('post_result_v3/safe_stop')
post_arrived = fact('post_result_v3/arrived')
wheel_trials = fact('legs/wheel_trials_at_band_heights')
wheel_pass = fact('legs/wheel_passes_at_band_heights')
leg_trials = fact('legs/band_gait_trials')
leg_clean = fact('legs/band_gait_clean_trials')
true_rocks = fact('legs/true_rocks')

gate_rows = facts['same_route']['suite_r2_v4_F3_002_gate']['rows']
gate = {r['vehicle']: r for r in gate_rows}
for vehicle in ['A', 'B', 'D']:
    r = gate[vehicle]
    for k in ['total_result', 'sim_seconds', 'looks', 'second_segment_result', 'legs_used']:
        assert r[k]['status'] == 'verified'
        assert sha(ROOT / r[k]['source']) == r[k]['source_sha256']
        bindings[f'F3_002/{vehicle}/{k}'] = r[k]
    assert r['second_segment_result']['value'] == 'not_run'
    assert not r['legs_used']['value']

live = facts['lux']['live_ledger_counts']
tallies = collections.Counter()
for ident, row in live['task_ids'].items():
    assert sha(ROOT / row['source']) == row['source_sha256'], ident
    tallies[row['status']] += 1
assert len(live['task_ids']) == live['created']
assert dict(tallies) == live['statuses']
same_count = facts['same_route']['completed_scenes']['value']
same_arrived = facts['same_route']['D_arrived_completed_scenes']['value']
same_paths = facts['same_route']['completed_scenes']['source_paths']
assert len(same_paths) == same_count * 4
assert all((ROOT / path).is_file() for path in same_paths)
same_D_paths = facts['same_route']['D_arrived_completed_scenes']['source_paths']
assert sum(json.loads((ROOT / path).read_text())['total_result'] == 'arrived' for path in same_D_paths) == same_arrived
world_count = len(shots['s05-world-grid']['sources'])
assert world_count == 12
film_facts = {'source_facts': str(OUT / 'facts.json'), 'source_facts_sha256': sha(OUT / 'facts.json'),
              'bindings': bindings, 'live_lux_counts': {'created': live['created'], 'statuses': dict(tallies), 'source': 'source_facts:/lux/live_ledger_counts', 'all_task_SHA_verified': True},
              'same_route': {'completed': same_count, 'D_arrived': same_arrived, 'source': 'source_facts:/same_route'},
              'rehearsal_worlds': {'value': world_count, 'source': str(OUT / 'shots/s05-world-grid.json'), 'source_sha256': sha(OUT / 'shots/s05-world-grid.json'), 'derivation': 'length of twelve original trajectory sources'},
              'mismatches': [], 'source_policy': 'Current source SHA checked; words and displayed numbers are generated from these bindings.'}
save(WORK / 'facts.json', film_facts)

# Each group is timed after its own narration is measured. This is also the
# pre-narration edit blueprint; it totals 185 seconds.
groups = []
def group(ident, chapter, seconds, parts, sentences):
    groups.append({'id': ident, 'chapter': chapter, 'base_duration_s': seconds, 'parts': parts,
                   'sentences': [{'id': f'{ident}-{i+1:02d}', 'text': text} for i, text in enumerate(sentences)]})
def part(ident, source, seconds, start=0, span=None, hold=False, label='', crop=None):
    return {'id': ident, 'shot': source, 'base_duration_s': seconds, 'source_start_s': start,
            'source_span_s': span, 'hold_frame': hold, 'label': label, 'crop': crop}

group('hook', '只看得到一面', 13,
      [part('opening', 's01-open-v2', 10, label='R1 · 原运行状态回放'), part('eye', 's02-eye-v2', 3, label='机器人原始观测 · 保存输入单帧')],
      ['月球南极，太阳贴着地平线，石头拖着长黑影。', '机器人只拍到朝着自己的一面。背面有什么？'])
group('comparison', '三种做法', 28, [{'id': 'comparison', 'type': 'shared_clock', 'base_duration_s': 28}],
      ['同一条路，同一机位，三种做法从同一时刻出发。',
       f'乐观车把没看见的当作没有，{decimal(O)}秒，碰撞。',
       f'Lux3D 想出背面，先检验再走：一眼，{decimal(I)}秒，到达。',
       f'保守车看了{integer(looks)}眼，{decimal(C)}秒后，仍然没有路。'])
group('model', '想象怎么被检验', 18,
      [part('photo', 'r04-photo-to-glb', 10, label='原照片与已有任务返回模型'),
       part('glbA', 'r02-glb-A', 4, label='Lux3D 原始 GLB · 官方 Aholo Viewer', crop=[405,185,560,490]),
       part('glbB', 'r03-glb-B', 4, label='另一块石头 · 原始 GLB 保留', crop=[405,185,560,490])],
      ['把照片交给 Lux3D，回来一整块石头，连看不见的背面也被补出来。',
       f'但看起来像，不等于真实。通过正面核对的{integer(count)}份想象里，{integer(short)}份背面短了{integer(short_threshold_cm)}厘米以上。'])
group('reveal', '想象怎么被检验', 9,
      [part('reveal', 'r01-reveal', 9, start=1, span=10, label='R1 · 原模型与真值叠合 · 事后诊断', crop=[380,455,500,440])],
      [f'正面通过了核对，这一份背面却短了{decimal(error,1)}米。'])
group('worlds', '想象怎么被检验', 12,
      [part('world', 's05-world-1-v2', 9, label='一份想象中的完整路线预演'),
       part('grid', 's05-world-grid', 3, start=3, span=3, label='多个准入世界 · 原预演记录')],
      ['所以我们生成多份、核对正面，再在每一份想象里预演完整路线，全部安全才迈步。',
       f'{integer(world_count)}个世界，都先走完。'])
group('results', '有用，也会出错', 24,
      [part('failure', 's06-failure', 24, label='F3_004 · 原事故连续记录 · 半速回放')],
      [f'{integer(decisive)}个决定性场景，预先按真实形状走通、乐观撞、保守停来选定。',
       f'在这{integer(decisive)}个别的做法都到不了的场景里，想象让机器人到了{integer(arrived)}个。',
       f'它也撞了{integer(collisions)}次，{integer(collisions)}次都留在页面上。',
       '这次就是原事故，画面连续保留。'])
group('post', '有用，也会出错', 9,
      [part('post', 's06-failure', 9, start=23.96, span=.03, hold=True, label='背景：原事故帧 · 右侧另列赛后统计')],
      [f'赛后收紧规则，{integer(post_count)}场没有碰撞，但{integer(post_stop)}场停车。更安全，也更常停。'])
group('wheel', '路上还有另一种石头', 4,
      [part('wheel', 's08-wheel', 4, start=.5, span=4, label='独立门槛预检查 · 轮行受阻')],
      ['路上还有矮门槛，轮子却过不去。'])
group('leg', '路上还有另一种石头', 16,
      [part('lift', 's08-lift', 14, label='同石独立预检查 · 完整抬轮、越过、落地'),
       part('depart', 's08-depart', 2, start=2, span=2, label='同一预检查记录 · 整车离开')],
      [f'同一高度带，轮行{integer(wheel_trials)}次，没有一次通过；逐轮抬腿，{integer(leg_trials)}次全部干净跨过。',
       '动作只用看见的几何，不靠想象。'])
group('connect', '路上还有另一种石头', 18,
      [part('connect', 's09-connect-overview-v2', 18, label='真实形状 · 连接预检查 · 不计正式车成绩')],
      ['两种石头连成一条路，先绕过高石，再穿门跨过门槛。',
       '这里用真实形状做连接预检查，转场处交接保存状态。不是正式车的到达成绩。'])
group('close', '路上还有另一种石头', 8,
      [part('close', 's09-connect-close-v2', 8, label='连接预检查 · 门槛近景 · 看见的几何')],
      ['门槛近景再看一次：抬轮、越过、落地。'])
group('stopA', '路上还有另一种石头', 7,
      [part('stopA', 's09-F3002-A-stop-v2', 7, label='正式 F3_002 · A/D 同轨迹 · 高石段停车')],
      ['换回想象，后石候选全被拒绝，车停了。'])
group('stopB', '路上还有另一种石头', 5,
      [part('stopB', 's09-F3002-B-stop-v2', 5, label='正式 F3_002 · B 轮触高石，由监视器停车')],
      ['只信看见的车，也在高石前停下。'])
group('ending', '先检验，再迈步', 14,
      [part('ending', 's03-imagination-v2', 14, start=15.5, span=5.3, label='R1 · 原到达尾段与终态保持')],
      [f'{integer(same_count)}个同路场景，想象车到达{integer(same_arrived)}个。',
       f'Lux3D 共创建{integer(live["created"])}个任务。', 'BeforeStep：先检验，再迈步。'])

selected = sorted({p['shot'] for g in groups for p in g['parts'] if 'shot' in p} |
                  {'s03-optimistic-v2', 's03-conservative-v2', 's03-imagination-v2'})
for name in selected:
    assert sha(OUT / 'shots' / (name + '.mp4')) == shots[name]['sha256']
plan = {'schema': 'beforestep-film-v6/v1', 'groups': groups, 'selected_shots': {n: shots[n] for n in selected},
        'duration_before_narration_s': sum(g['base_duration_s'] for g in groups), 'target_duration_s': [170, 190],
        'facts_file': str(WORK / 'facts.json'), 'facts_sha256': sha(WORK / 'facts.json'),
        'current_lux_counts': {'created': live['created'], **dict(tallies)},
        'r1': {'optimistic': O, 'conservative': C, 'imagination': I},
        'decisive': {'count': decisive, 'arrived': arrived, 'stopped': stopped, 'collisions': collisions},
        'post': {'count': post_count, 'arrived': post_arrived, 'stopped': post_stop, 'collisions': post_collisions},
        'legs': {'wheel_trials': wheel_trials, 'wheel_passes': wheel_pass, 'leg_trials': leg_trials, 'leg_clean': leg_clean, 'true_rocks': true_rocks},
        'same_route': {'scenes': same_count, 'D_arrived': same_arrived},
        'back_error': {'candidate_count': count, 'short': short, 'reveal_m_rounded': round(error, 2)},
        'gate': {v: {'seconds': gate[v]['sim_seconds']['value'], 'looks': gate[v]['looks']['value']} for v in ['A', 'B', 'D']},
        'authority_SHA': {p.name: sha(p) for p in [OUT / 'instructions/STORY_V3.md', OUT / 'instructions/NOTE_FOR_CODEX_ACT5.md']},
        'new_physics_runs': 0, 'new_Lux3D_tasks': 0, 'music': False, 'gpu_shutdown': False}
save(WORK / 'plan.json', plan)
transcript = '\n\n'.join(g['chapter'] + '\n' + '\n'.join(s['text'] for s in g['sentences']) for g in groups)
(WORK / 'narration.md').write_text('# BeforeStep 成片配音与字幕同稿\n\n' + transcript + '\n')
state = load_state(WORK / 'state.json')
state.update(status='script_and_fact_bindings_ready', next='Synthesize sentence audio; set shot timings from actual audio; compose retained shots',
             plan=str(WORK / 'plan.json'), narration=str(WORK / 'narration.md'))
save(WORK / 'state.json', state)
status('成片事实核验与文案完成', WORK / 'plan.json',
       f'通过：实际源SHA/491任务账本核对；五幕+ACT5，预计{plan["duration_before_narration_s"]}秒；当前生成数491/460/31，真值预检查与正式停车分清')
print(json.dumps({'duration_s': plan['duration_before_narration_s'], 'narration_sentences': sum(len(g['sentences']) for g in groups),
                  'narration_characters': sum(len(s['text']) for g in groups for s in g['sentences']), 'source_shots': len(selected)}, ensure_ascii=False))

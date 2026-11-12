"""Resume-safe local training/evaluation coordinator; no Lux generation or publishing.

Waits for the already recorded prechecks. It stops if a gate fails and never
uses validation/test outcomes to change the generator or protocol.
"""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experimental.arena.common import OUT,read,write,sha


def protocol():
    cfg=read(ROOT/'experimental/arena/parameters.json');lib=read(ROOT/cfg['capsule_library'])
    capsules={side:[c['id'] for c in lib['capsules'] if c['eligible'] and c['split']==side and c.get('source_look') in cfg['source_looks']] for side in ['training_side','heldout']}
    seeds={k:cfg[k] for k in ['development','train','validation','sealed','ood','fidelity']}
    text=f'''# Arena v2 预注册

在任何验证、封存或分布外结果产生之前提交。参数、数据划分、方法、阈值选法和标准此后不修改。

参数文件：`experimental/arena/parameters.json`，SHA256 `{sha(ROOT/'experimental/arena/parameters.json')}`。
真实胶囊库：`{cfg['capsule_library']}`，SHA256 `{sha(ROOT/cfg['capsule_library'])}`。
种子区间（起点与数量）：`{json.dumps(seeds,sort_keys=True)}`。全部与navigation_v1种子互斥。
训练侧胶囊：`{json.dumps(capsules['training_side'])}`；封存胶囊：`{json.dumps(capsules['heldout'])}`。
封存六场景：`{json.dumps(lib['heldout_scenes'])}`。留出布局、摆位、Lux结果；无单独石种留出，背景使用全部12种已存扫描。

5cm网格，范围[-1,13]×[-2,2.5]，六状态。生产RGB-D：冻结N.observe，4040×3030缩至1600×1200。每场最多{cfg['max_looks']}次显式停看，每眼{cfg['look_seconds']}秒，两眼之间无观测。初始1m已知空地为所有方法共有的生成器先验，生成时核验，侵入时取消；NOGO仍禁止通行。Lux只在匹配原视角的第一眼提供，后眼不生成新结果，只保留第一眼缓存先验。

石头及全部候选、相机和太阳按整体刚体变换；当前相机距离比1、视线和太阳相对方位偏差0。额外无想象石在源拍摄目标之后，窄缝按参数显式构造。已有Lux结果移植到近似原视角，新增Lux付费0；不能表述为为新照片生成。

方法：保守未知阻挡；乐观未知空地；原想象规则调用冻结N.occupancy(imagination)及冻结五指标准入；严格规则调用N.occupancy(imagination_strict)、一格足迹安全膨胀与冻结SH阴影计算；严格+LLM从严格数值路线/再看/停车的有限选项中裁决，失败回退；学习CNN预测未知占据，数值规划；同CNN去掉全部Lux通道消融；see_dark是相同RGB-D观测取消黑像素屏蔽的保守参照。

规划直行/转弯半径0.40/0.57m；几何接触代理使用实际机器人0.33/0.50m，区别于7cm安全缓冲。MuJoCo实际接触独立报告。所有方法同一规划器、预算、感知、初始化和底层规则控制。真值仅用于教师标签、碰撞、可达性统计与诊断，推理不读取。

网络22通道卷积编码/空洞卷积/插值解码，输出每格占据概率；监督为未观测格的真实占据，用未加类别权重BCE。4000训练世界，15轮AdamW(lr=.001,weight_decay=.0001)，batch8，CPU4线程，种子20261112；最佳权重按最低训练损失，两个版本同种子/数据/架构/轮数，消融仅清零Lux通道6:15。不使用决策头，不要求DAgger，不使用合成想象评分。

风险阈值候选固定为[0.0,0.05,0.1,0.2,0.4,0.7]；仅在300验证世界上选择。要求碰撞≤min(3%,严格规则+1个百分点)，取到达最高，依次以碰撞更低、阈值更低打破平局；若没有安全点，取碰撞最低、到达最高、阈值最低并明确无安全工作点。路线按扫过车身的概率汇总，同时未知高概率格阻挡；已观测障碍硬门卫不变。

500封存、300更密OOD只跑一次，每种方法同一世界成对。完整分母保留不可达、碰撞、停车。记录到达/碰撞/安全停车、眼数、含观察的几何耗时、实际规划/LLM等待、路径长度；所有世界和真值规划可达世界分别统计。按胶囊分组，并按胶囊聚类自助2000次，随机种子20261112，百分位95%区间。

达标：学习碰撞≤严格+1pp且≤3%；到达≥严格+10pp；无规则同时到达更高且碰撞更低。不放宽标准，不在封存上调参。Lux消融在验证选择的同一安全上限下报告；LLM与严格/学习在同批150个验证、前150封存上成对。LLM开发最多50请求，新账本全轮最多3000，解析最多重试一次（计预算），连续5次401/403停止LLM且继续其他部分。JSON支持时启用，输出上限8192，温度0，每次发送前落盘，未完成请求不重发。

物理确认：前24封存种子，乐观/严格/学习全部运行。真实6留出新策略5眼零样本，调用冻结库与记录观测/缓存Lux，新增付费0；与原R3结果并排，原字节不改。
'''
    return text


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--memory');ap.add_argument('--precheck-only',action='store_true');ap.add_argument('--development-check',default='development-production-5');a=ap.parse_args()
    ledger=OUT/'jobs.json';jobs=read(ledger) if ledger.exists() else {'schema':'beforestep-arena-jobs/v2','jobs':{},'new_lux_tasks':0}
    def checkpoint(event):
        jobs['last_event']=event;jobs['updated_at']=datetime.now(timezone.utc).isoformat();write(ledger,jobs)
        if a.memory:
            p=Path(a.memory)
            with p.open('a') as f:f.write('\n- Arena coordinator checkpoint '+json.dumps({'event':event,'ledger':str(ledger),'utc':jobs['updated_at']},ensure_ascii=False)+'\n')
    def execute(name,command):
        previous=jobs['jobs'].get(name)
        if previous and previous.get('status')=='complete':return
        if previous and previous.get('pid') and Path(f"/proc/{previous['pid']}").exists():raise RuntimeError('Existing live job; inspect and do not duplicate '+name)
        log=OUT/'logs'/f'{name}.log';log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('a') as f:
            p=subprocess.Popen(command,cwd=ROOT,env={**os.environ,'MUJOCO_GL':'egl','OPENBLAS_NUM_THREADS':'1'},stdout=f,stderr=subprocess.STDOUT)
            jobs['jobs'][name]={'status':'running','pid':p.pid,'command':command,'log':str(log.relative_to(ROOT))};checkpoint('started '+name)
            code=p.wait()
        jobs['jobs'][name]['status']='complete' if code==0 else 'failed';jobs['jobs'][name]['exit_code']=code;checkpoint('finished '+name)
        if code:raise RuntimeError(f'{name} failed ({code}); retain identity and inspect log')
    checks=[OUT/'prechecks'/a.development_check/'summary.json',OUT/'prechecks/transplant-fidelity-final/summary.json']
    checkpoint('waiting for final prechecks')
    while not all(p.exists() for p in checks):time.sleep(10)
    assert all(read(p)['passed'] for p in checks),'A precheck failed; no preregistration/training/test will start'
    write(OUT/'prechecks/final.json',{'passed':True,'development':str(checks[0].relative_to(ROOT)),'fidelity':str(checks[1].relative_to(ROOT)),'files_sha256':{str(p.relative_to(ROOT)):sha(p) for p in checks},'sensor_fallback':'production RGB-D; approximate sensor failed 77.0465%/64.7059%'})
    checkpoint('final prechecks passed')
    if a.precheck_only:return
    file=ROOT/'docs/arena-protocol.md'
    if not file.exists():
        file.write_text(protocol())
        frozen=['docs/arena-protocol.md', 'experimental/arena/parameters.json', read(ROOT/'experimental/arena/parameters.json')['capsule_library']]
        frozen += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'experimental/arena').glob('*.py'))]
        write(OUT/'protocol.json',{'protocol_sha256':sha(file),'frozen_files_sha256':{p:sha(ROOT/p) for p in frozen}})
        subprocess.run(['git','add','docs/arena-protocol.md','docs/reviews/RESULT_ARENA_LEARNING.md','docs/reviews/SPEC_ARENA_LEARNING.md','experimental/arena','tests/test_arena.py','ops/arena_pipeline.py','ops/arena_resume_after_development.py','ops/restore_arena_inputs.py','requirements-arena.txt','.gitattributes','assets/runtime-arena-real-inputs.tar.gz','assets/runtime-arena-capsule-metadata.tar.gz','evidence/learning/arena_v2'],cwd=ROOT,check=True)
        subprocess.run(['git','commit','-m','Preregister faithful sparse-observation arena and hidden occupancy learning'],cwd=ROOT,check=True)
    registration=read(OUT/'protocol.json')
    if 'commit' not in registration:
        registration['commit']=subprocess.check_output(['git','log','-1','--format=%H','--','docs/arena-protocol.md'],cwd=ROOT,text=True).strip()
        assert registration['commit'],'Protocol is not committed'
        write(OUT/'protocol.json',registration)
    from experimental.arena.registration import require_registration
    require_registration();checkpoint('protocol committed '+registration['commit'])
    publication=OUT/'protocol-remote.json'
    if not publication.exists():
        subprocess.run(['git','push','origin','main'],cwd=ROOT,check=True)
        remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        assert remote==registration['commit'],'Remote preregistration differs from local committed protocol'
        write(publication,{'commit':remote,'published_before_training_validation_test':True,'utc':datetime.now(timezone.utc).isoformat()})
        checkpoint('protocol pushed and remote main verified '+remote)
    py=sys.executable;training=OUT/'training';data=OUT/'training-data'
    execute('training-data',[py,'-m','experimental.arena.train','generate','--out',str(data),'--split','train','--workers','2'])
    for name,flags in [('lux',[]),('no_lux',['--no-lux'])]:
        execute('train-'+name,[py,'-m','experimental.arena.train','train','--data',str(data),'--out',str(training/name),*flags])
    lux=training/'lux/best.pt';no=training/'no_lux/best.pt'
    execute('llm-smoke',[py,'-m','experimental.arena.llm_suite','--stage','smoke','--out',str(OUT/'llm/smoke')])
    execute('validation-data',[py,'-m','experimental.arena.train','generate','--out',str(OUT/'validation-data'),'--split','validation','--workers','2'])
    execute('validation',[py,'-m','experimental.arena.cli','evaluate','--split','validation','--out',str(OUT/'validation'),'--lux',str(lux),'--no-lux',str(no),'--thresholds','0','0.05','0.1','0.2','0.4','0.7'])
    for name,model,no_lux in [('lux',lux,False),('no_lux',no,True)]:
        from experimental.arena.train import calibration
        target=OUT/'calibration'/f'{name}.json'
        if not target.exists():calibration(OUT/'validation-data',model,target,no_lux)
    execute('llm-validation',[py,'-m','experimental.arena.llm_suite','--stage','validation','--out',str(OUT/'llm/validation')])
    for split in ['sealed','ood']:
        execute(split,[py,'-m','experimental.arena.cli','evaluate','--split',split,'--out',str(OUT/split),'--lux',str(lux),'--no-lux',str(no)])
        if split=='sealed':
            execute('llm-sealed',[py,'-m','experimental.arena.llm_suite','--stage','sealed','--out',str(OUT/'llm/sealed')])
            execute('real-heldouts',[py,'-m','experimental.arena.physical_suite','--real','--out',str(OUT/'real-heldouts'),'--model',str(lux),'--workers','1'])
    execute('sealed-physics',[py,'-m','experimental.arena.physical_suite','--out',str(OUT/'physical'),'--model',str(lux),'--workers','2'])
    checkpoint('All training, calibration, paired LLM, one-time sealed/OOD and physical/real episodes complete')
    subprocess.run([py,str(ROOT/'ops/publish_arena.py')],cwd=ROOT,check=True)


if __name__=='__main__':main()

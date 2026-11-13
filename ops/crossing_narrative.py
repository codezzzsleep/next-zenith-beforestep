"""Apply the SPEC opening and evidence-derived crossing chapter only."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    spec=(ROOT/'docs/reviews/SPEC_WHEELLEG_CROSSING.md').read_text()
    opening=re.search(r'^> (对轮子来说.*)$',spec,re.M).group(1)
    for relative in ['README.md','docs/report.md']:
        p=ROOT/relative;text=p.read_text();marker='<!-- PHOTO-STORY-'+('README' if relative=='README.md' else 'REPORT')+'-START -->'
        prefix,rest=text.split(marker+'\n',1);old,tail=rest.split('\n\n',1)
        p.write_text(prefix+marker+'\n'+opening+'\n\n'+tail)
    gate=json.loads((ROOT/'evidence/crossing/calibration/gate.json').read_text())
    capacity=json.loads((ROOT/'evidence/crossing/calibration/capability-v72.json').read_text())
    wheel=max(g['height_m'] for g in capacity['groups'] if g['method'] in ['fixed','high'] and g['passed'])
    band=[r for r in gate['necessary_by_height'] if r['d_max_m'] and r['height_m']>wheel]
    narrow=json.loads((ROOT/'evidence/crossing/development-narrow-summary.json').read_text())
    chapter='\n## 轮腿跨越\n\n'
    chapter+=f'同一台轮腿机器人，固定腿姿轮行实测最高通过 {wheel*100:g} 厘米。逐轮跨越在采样的 '+ '、'.join(f'{r["height_m"]*100:g}' for r in band)+' 厘米高度形成必要带，各高度的最大已验进深分别为 '+ '、'.join(f'{r["d_max_m"]*100:g}' for r in band)+' 厘米。采样点之间没有连续高度实测；完整能力表和真实接触记录公开保留。\n\n'
    chapter+=f'窄门槛开发生成 {narrow["candidate_count"]} 个候选，{narrow["invalid_wheel_passable"]} 个被轮子滚过作废，剩 {narrow["valid_count"]} 个有效。A 过不去是有效场景的定义，不是实验发现；“非腿不可”的事实来自能力标定。真值诊断 E 和可见部分 B 的逐场结果见跨越报告；E 始终不是 Lux3D 的成绩。\n\n'
    chapter+='完整三维不是直接的行动答案。每份真实生成先核对可见观测，跨越位置必须处于所有准入模型的能力范围内，再在每份模型里完整预演，全部干净通过才实走。首场已有准入模型，但所有候选位置的包络进深都超出冻结能力限制，D 停止且未进行物理预演。\n\n'
    chapter+='跨越仍处开发阶段，未预注册，正式测试为 0 场；尚无 Lux3D 跨越锚点、跨越画面帧或本轮最终 PDF。矮石头沿轮迹的未知部分应按实际几何量报告，不能把概念上的“另一半”当作这些场景的测量结论。R1–R3 的绕行、拒绝与碰撞证据继续保留。\n\n'
    chapter+='[轮腿能力与开发页面](https://codezzzsleep.github.io/next-zenith-beforestep/crossing.html) · [完整跨越报告](crossing.md) · [窄门槛标定](reviews/RESULT_CROSSING_NARROW_GENERATOR.md)。\n'
    p=ROOT/'docs/report.md';text=p.read_text();marker='\n## 轮腿跨越\n'
    if marker in text:text=text.split(marker)[0]
    p.write_text(text+chapter)
    p=ROOT/'docs/hackathon-submission.md';text=p.read_text();marker='\n## 轮腿跨越入口\n'
    if marker in text:text=text.split(marker)[0]
    p.write_text(text+marker+'\n[轮腿能力与开发页面](https://codezzzsleep.github.io/next-zenith-beforestep/crossing.html) · [报告](crossing.md)。本轮正式测试、锚点与新画面素材尚未完成，进度以最新跨越 RESULT 为准。\n')
    print(json.dumps({'spec_opening_applied':True,'wheel_max_m':wheel,'formal_test_scenes':0,'pdf_generated':False}))

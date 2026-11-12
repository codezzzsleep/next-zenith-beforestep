"""Align submission prose with the delivered photo-to-whole-rock homepage."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def replace_block(text,start,end,body,insert_after=None):
 block=f'<!-- {start} -->\n{body}\n<!-- {end} -->\n\n';pattern=f'<!-- {start} -->[\\s\\S]*?<!-- {end} -->\\n*'
 if re.search(pattern,text):return re.sub(pattern,lambda _:block,text)
 return text.replace(insert_after,insert_after+block,1) if insert_after else block+text

def main():
 data_path=ROOT/'evidence/award/home-contract/assets/data/site.json';d=json.loads(data_path.read_text());g=json.loads((ROOT/'site/data/gallery.json').read_text())['stats'];k=d['stats']['known_decisive']['imagination'];h=d['stats']['holdout']['imagination'];strict=d['stats']['holdout']['imagination_strict'];known=d['stats']['known_all']['imagination_strict'];anchor=d['runs']['imagination'];failures=[r['scene'] for r in d['known']+d['holdouts'] if r['runs']['imagination']['result']=='collision'];cf=d['counterfactuals']
 story='机器人只拍到石头的一面。Aholo Lux3D 把这张平面照片变成包含未知背面的完整三维石头；机器人先对照可见观测检查，再在每个采纳的想象世界里走完路线，最后在独立仿真里执行。月面和低角度阳光提供实验背景，核心是从照片生成的几何改变行动判断。'
 summary=story+f'\n\n锚点真实 Lux 分支{anchor["looks"]}眼、{anchor["sim_time_s"]}秒到达（仿真行程，不含云端生成墙钟），首眼{d["generation"]["tasks"]}个真实任务返回{d["generation"]["succeeded"]}个模型、{d["generation"]["failed"]}个供应商失败。陈列室保留全部{g["returned_models"]}份既有真实生成模型。\n\n'
 total_scenes=len([r for r in d['known'] if r['classification']=='decisive'])+len(d['holdouts']);total_arrived=k['arrived']+h['arrived'];total_collisions=k['collision']+h['collision']
 summary+=f'原{len([r for r in d["known"] if r["classification"]=="decisive"])}个已知决定性场景：{k["arrived"]}到达/{k["stuck"]}停车/{k["collision"]}碰撞；{len(d["holdouts"])}个指定留出：原想象{h["arrived"]}到达/{h["stuck"]}停车/{h["collision"]}碰撞，最终v3赛后修订{strict["arrived"]}到达/{strict["stuck"]}停车/{strict["collision"]}碰撞。首页的{total_scenes}场/{total_arrived}到达/{total_collisions}碰撞是两个分层的算术相加，技术结论分别报告；全{len(d["known"])}个已知复测为{known["arrived"]}到达/{known["stuck"]}停车/{known["collision"]}碰撞。\n\n'
 summary+='四次原方法碰撞均保留：'+ '、'.join(failures)+'。F1_020碰到从未形成观测目标的C；另外三场低估B背面，正面自检与所有预演通过后仍实际接触。early oldv2 F1_003碰撞另列。'
 summary+=f'原拒绝反事实{cf["r2"]["collisions"]}/{cf["r2"]["executed"]}碰撞，R3已知{cf["r3"]["known_frozen"]["collisions"]}/{cf["r3"]["known_frozen"]["executed"]}、留出{cf["r3"]["designated_holdout"]["collisions"]}/{cf["r3"]["designated_holdout"]["executed"]}，合计{cf["r2"]["executed"]+sum(v["executed"] for v in cf["r3"].values())}次干预、{cf["r2"]["collisions"]+sum(v["collisions"] for v in cf["r3"].values())}次碰撞；干预次数不等于独立生成资产份数。\n\n[作品首页](../site/index.html) · [全部想象](../site/gallery.html) · [真假叠合](../site/overlays.html) · [数字审计](../evidence/award/acceptance/home-numbers.json)。'
 report=ROOT/'docs/report.md';text=report.read_text();text=re.sub(r'^# [^\n]+','# 先见一步：一张照片，变成一整块石头',text,count=1);text=replace_block(text,'PHOTO-STORY-REPORT-START','PHOTO-STORY-REPORT-END',summary,insert_after=text.splitlines()[0]+'\n\n');report.write_text(text)
 readme=ROOT/'README.md';text=readme.read_text();text=replace_block(text,'PHOTO-STORY-README-START','PHOTO-STORY-README-END',story+'\n\n[转着看真实生成的石头](https://codezzzsleep.github.io/next-zenith-beforestep/) · [想象陈列室](https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html)。',insert_after='# 先见一步 · BeforeStep\n\n');readme.write_text(text)
 promotion=ROOT/'docs/award-promotion.md';text=promotion.read_text();text=text.replace('可体验： https://codezzzsleep.github.io/next-zenith-beforestep/levels.html','可体验： https://codezzzsleep.github.io/next-zenith-beforestep/\n全部真实生成： https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html')
 text=text.replace('项目名：BeforeStep / 先见一步。核心是','项目名：BeforeStep / 先见一步。一张真实照片变成包含未知背面的完整三维石头。核心是');text=text.replace('Notebook 从公开源码安装，使用已有观测与 Lux 结果复现','Notebook 从公开源码安装，按 README 执行 `git lfs install --local`、LFS拉取和依赖安装，再运行 `.venv/bin/python ops/quickstart.py --reuse-lux`，使用已有观测与 Lux 结果复现');promotion.write_text(text)
 facts={'schema':'beforestep-award-photo-story-alignment/v1','source_data':str(data_path.relative_to(ROOT)),'source_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),'homepage_arithmetic_total_scope':'known decisive plus designated holdouts; no pooled generalization claim','gallery':g,'known_decisive':k,'holdout_original':h,'holdout_revision':strict,'all_known_revision':known,'collision_scenes':failures,'counterfactuals_by_scope':cf,'prose_files':['docs/report.md','README.md','docs/award-promotion.md'],'homepage_design_changed':False}
 (ROOT/'evidence/award/acceptance/C8-story.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'files':len(facts['prose_files']),'gallery_models':g['returned_models'],'collision_scenes':failures,'homepage_design_changed':False}))
if __name__=='__main__':main()

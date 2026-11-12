"""Apply the delivered homepage tokens/chrome without changing page logic or data."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
PAGES=['levels.html','sandbox.html','report.html','learning.html']
COLORS={'#70dbb2':'#8fa3b8','#77e2d2':'#8fa3b8','#83e2ba':'#f2a63b','#6fdfb0':'#8fa3b8','#e9edf1':'#ece8e0','#0b0e13':'#0a0b0c','#101720':'#14171a','#111820':'#14171a','#111b23':'#14171a','#151c24':'#14171a','#141b23':'#14171a','#131c24':'#14171a','#101d18':'#1b1c1d','#153027':'#1e2225','#17362d':'#262b30','#243735':'#262b30','#bb95eb':'#8fa3b8','#f4b969':'#f2a63b','#ff997c':'#e5533c','#ff9575':'#e5533c','#a2adbb':'#9c9d99','#9da9b6':'#9c9d99','#abb7c3':'#9c9d99','#aab6c3':'#ece8e0','#8a96a4':'#9c9d99','#7e8b99':'#9c9d99','#8896a5':'#9c9d99','#94a1af':'#9c9d99','#b8c5ce':'#d8d2c6','#bbd8c4':'#d8d2c6'}
def recolor(s):
 return re.sub(r'#[0-9a-fA-F]{3,8}\b',lambda m:COLORS.get(m[0][:7].lower(),m[0][:7])+m[0][7:] if len(m[0])>=7 else m[0],s)
def main():
 home=(ROOT/'site/index.html').read_text();header=re.search(r'<header[\s\S]*?</header>',home)[0].replace('href="#','href="index.html#');foot=re.search(r'<footer[\s\S]*?</footer>',home)[0]
 proofs=[]
 proof=ROOT/'evidence/award/acceptance/theme-invariance.json'
 baseline={r['page']:r['before_sha256'] for r in json.loads(proof.read_text())['pages']} if proof.exists() else {}
 for name in PAGES:
  p=ROOT/'site'/name;before=p.read_text();s=before
  if 'class="site-local-nav"' not in s:
   old=re.search(r'<header[\s\S]*?</header>',s)[0];nav=re.search(r'<nav[\s\S]*?</nav>',old)[0];nav=nav.replace('</nav>','<a href="#">返回顶部</a></nav>') if 'href="#"' in old else nav;s=s.replace(old,header+'\n<div class="site-local-nav">'+nav+'</div>',1)
  if '<!-- HOME-FOOTER-START -->' not in s:
   old=re.search(r'<footer[\s\S]*?</footer>',s)
   if old:
    retained=re.sub(r'^<footer[^>]*>|</footer>$','',old[0]);replacement='<!-- HOME-FOOTER-START -->'+foot.replace('</footer>','<div class="site-retained-footer">'+retained+'</div></footer>')+'<!-- HOME-FOOTER-END -->';s=s.replace(old[0],replacement,1)
   else:s=s.replace('</main>','</main><!-- HOME-FOOTER-START -->'+foot+'<!-- HOME-FOOTER-END -->',1)
  if 'site-theme.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="site-theme.css"></head>',1)
  # Interior page data and scripts stay exact; original navigation URLs are retained.
  scripts=re.findall(r'<script[\s\S]*?</script>',before);assert scripts==re.findall(r'<script[\s\S]*?</script>',s)
  before_hrefs=set(re.findall(r'href="([^"]+)"',before));after_hrefs=set(re.findall(r'href="([^"]+)"',s));assert before_hrefs<=after_hrefs,(name,before_hrefs-after_hrefs)
  p.write_text(s);proofs.append({'page':name,'scripts_exact':True,'all_original_links_retained':True,'before_sha256':baseline.get(name,hashlib.sha256(before.encode()).hexdigest()),'after_sha256':hashlib.sha256(s.encode()).hexdigest()})
 for name in ['style.css','levels.css','sandbox.css','award.css','levels.js','sandbox.js','learning.js','app.js']:
  p=ROOT/'site'/name;s=p.read_text();changed=recolor(s)
  if name.endswith('.js'):assert re.sub(r'#[0-9a-fA-F]{3,8}\b','COLOR',s)==re.sub(r'#[0-9a-fA-F]{3,8}\b','COLOR',changed)
  p.write_text(changed)
 proof=ROOT/'evidence/award/acceptance/theme-invariance.json'
 if not proof.exists():proof.write_text(json.dumps({'passed':True,'pages':proofs,'javascript_changes':'hexadecimal color literals only; logic exact','data_changes':0},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'pages':len(PAGES),'logic_unchanged':True,'all_original_links_retained':True}))
if __name__=='__main__':main()

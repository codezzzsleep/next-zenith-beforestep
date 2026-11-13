"""Build the complete current report HTML; PDF requires a separate final step."""
import posixpath,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import markdown

if __name__=='__main__':
    text=(ROOT/'docs/report.md').read_text()
    text=text.replace('R1 新 Demo 由负责人使用完整保存数据制作','新版 Demo 由 Agent 按负责人分镜合成，使用真实保存数据与公网页面录屏')
    text=text.replace('The project lead prepares the new video from the supplied real run data.','The agent composes the new video from the supplied real run data and the lead’s storyboard.')
    (ROOT/'docs/report.md').write_text(text)
    html=markdown.markdown(text,extensions=['tables','fenced_code','toc'])
    def asset(match):
        kind,path=match.group(1),match.group(2)
        if path.startswith(('https://','http://','#','data:')):return match.group(0)
        relative=posixpath.normpath('docs/'+path)
        if kind=='src':target=relative.removeprefix('site/')
        elif relative.endswith('.md') or '.md#' in relative:target='https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/'+relative
        else:target=relative.removeprefix('site/')
        return f'{kind}="{target}"'
    html=re.sub(r'(src|href)="([^"]+)"',asset,html)
    style='''@page{size:A4;margin:15mm}body{max-width:900px;margin:30px auto;padding:0 18px;color:#202a30;font:14px/1.75 "WenQuanYi Zen Hei",sans-serif;overflow-wrap:anywhere}h1{font-size:29px}h2{margin-top:28px;break-after:avoid}h3{break-after:avoid}p,li{orphans:3;widows:3}img{max-width:100%;height:auto;break-inside:avoid}table{border-collapse:collapse;width:100%;font-size:11px}th,td{border:1px solid #b7bfc2;padding:6px;vertical-align:top;overflow-wrap:anywhere}a{color:#236a5c}pre{white-space:pre-wrap}code{font-size:11px}@media print{body{margin:0;padding:0}img{max-height:235mm;object-fit:contain}table{break-inside:auto}tr{break-inside:avoid}}'''
    page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BeforeStep · 完整项目报告</title><style>'+style+'</style></head><body>'+html+'</body></html>'
    (ROOT/'site/report.html').write_text(page)
    print('Current report HTML built; PDF has not been generated.')

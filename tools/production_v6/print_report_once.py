"""Print the supplied final self-contained HTML once, then rasterize via PDFium.

Usage: PYTHONPATH=/tmp/beforestep-browser-deps:/tmp/beforestep-pdf-deps
 python3 print_report_once.py --html /path/to/final/report.html
The ledger's reserved/printed state forbids a second Chromium PDF call, including
after interruption. Page PNG recovery reads the existing PDF without printing.
"""
import argparse,asyncio,json,os,shutil,re,sys,fcntl
from pathlib import Path
from common import *
DIRECTORY=OUT/'report';DIRECTORY.mkdir(exist_ok=True);LEDGER=DIRECTORY/'print-ledger.json'
async def print_once(source):
 from playwright.async_api import async_playwright
 with (DIRECTORY/'print.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if LEDGER.exists():raise RuntimeError('A print reservation already exists. Never reprint; inspect ledger and recover PNGs from its existing PDF.')
  html=source.read_text();images=re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)',html,re.I)
  if any(not src.startswith('data:image/') for src in images):raise RuntimeError('Report HTML must contain self-contained image data before the single print.')
  destination=DIRECTORY/'report.html'
  if source.resolve()!=destination.resolve():
   if destination.exists() and destination.read_bytes()!=source.read_bytes():raise RuntimeError('A different report.html is already present; preserve its author version before replacing.')
   shutil.copyfile(source,destination)
  record={'status':'html_verified','source':str(source),'html':str(destination),'html_sha256':sha(destination),'print_calls':0,'pdf':str(DIRECTORY/'report.pdf'),'requested_format':'A4','self_contained_image_count':len(images)}
  save(DIRECTORY/'html-verification.json',record);status('D 报告HTML就位',destination,'通过：自含图片、原作者HTML逐SHA保全')
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
   page=await browser.new_page(viewport={'width':1200,'height':1600})
   await page.goto(destination.as_uri(),wait_until='load');await page.evaluate('document.fonts.ready')
   complete=await page.evaluate('Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)')
   if not complete:raise RuntimeError('At least one author image is not decoded; no print occurred.')
   await page.emulate_media(media='print')
   # Persist the only permission to call page.pdf before that irreversible count.
   record.update(status='reserved_single_print',print_calls=1,pid=os.getpid());save(LEDGER,record)
   await page.pdf(path=str(DIRECTORY/'report.pdf'),format='A4',print_background=True,display_header_footer=False,prefer_css_page_size=False)
   record.update(status='printed_once',pdf_sha256=sha(DIRECTORY/'report.pdf'),bytes=(DIRECTORY/'report.pdf').stat().st_size);record.pop('pid',None);save(LEDGER,record)
   await browser.close()
  status('D Chromium A4 PDF唯一打印',DIRECTORY/'report.pdf','通过：print_calls=1；PDFium逐页渲染接续')
def rasterize():
 import pypdfium2 as pdfium
 record=json.loads(LEDGER.read_text());pdf=Path(record['pdf'])
 if not pdf.is_file():raise RuntimeError('Reserved print has no durable PDF; do not issue a second print.')
 if record.get('pdf_sha256') and sha(pdf)!=record['pdf_sha256']:raise RuntimeError('Existing PDF changed; inspect without reprinting.')
 doc=pdfium.PdfDocument(str(pdf));pages=DIRECTORY/'pages';pages.mkdir(exist_ok=True);rows=[]
 for i in range(len(doc)):
  page=doc[i];image=page.render(scale=2).to_pil();path=pages/f'page-{i+1:02d}.png';image.save(path)
  rows.append({'page':i+1,'path':str(path),'sha256':sha(path),'size_px':list(image.size),'size_pt':list(page.get_size())});page.close()
 doc.close();save(pages/'index.json',{'pdf':str(pdf),'pdf_sha256':sha(pdf),'renderer':'PDFium','scale':2,'pages':rows,'visual_acceptance':'待负责人逐页看，未自行标视觉通过'})
 record.update(status='printed_once_pages_ready',page_count=len(rows),pages_index=str(pages/'index.json'));save(LEDGER,record)
 status('D PDFium逐页PNG',pages/'index.json',f'通过：{len(rows)}页；待负责人逐页看')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--html',type=Path);ap.add_argument('--pages-only',action='store_true');args=ap.parse_args()
 if not args.pages_only:
  if not args.html:ap.error('--html required for the author supplied final HTML')
  asyncio.run(print_once(args.html))
 rasterize()

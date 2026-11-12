"""Check the four themed pages' actual computed tokens and mobile layout."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8101/');p.add_argument('--name',default='C3-theme-local');a=p.parse_args();out=ROOT/'evidence/award/acceptance';errors=[];http=[];rows=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',args=['--no-sandbox','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  for name in ['levels.html','sandbox.html','report.html','learning.html']:
   page.goto(urljoin(a.url,name),wait_until='networkidle');assert page.locator('header.bar .brand').inner_text()=='先见一步BeforeStep';assert page.locator('footer.foot').count()==1
   assert page.evaluate('getComputedStyle(document.body).backgroundColor')=='rgb(10, 11, 12)';assert page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--lamp").trim()')=='#f2a63b'
   assert 'PingFang SC' in page.evaluate('getComputedStyle(document.body).fontFamily');page.screenshot(path=str(out/(a.name+'-'+name.removesuffix('.html')+'-1440.png')),full_page=True);page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/(a.name+'-'+name.removesuffix('.html')+'-390.png')),full_page=True);page.set_viewport_size({'width':1440,'height':1000});rows.append(name)
  assert not errors,errors;assert not http,http;b.close()
 result={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'pages':rows,'url':a.url,'tokens_font_chrome_match':True,'mobile_390_no_overflow':True,'errors':errors,'http_errors':http};(out/(a.name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()

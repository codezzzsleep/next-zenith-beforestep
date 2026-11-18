"""Pair real browser startups while changing only the startup CDN choice.

Requires Python Playwright and Chromium. No physics or pose is injected.
The current deployed renderer is measured; archived samples name their version.
"""
import argparse, asyncio, json, time
from pathlib import Path
from playwright.async_api import async_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='https://codezzzsleep.github.io/next-zenith-beforestep')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--chromium')
parser.add_argument('--pairs',type=int,default=7)
parser.add_argument('--slow-pairs',type=int,default=3)
args=parser.parse_args()

async def main():
    report={'url':args.url,'method':'Fresh context for each cold visit; same-context normal reload; HTTP caching enabled. Same HTML, original assets and physical simulation. Only startup mirror flags change.','samples':[],'passed':False}
    def save():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path=args.chromium,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        try:
            for mbps,count in [(0,args.pairs),(4,args.slow_pairs)]:
                for pair in range(count):
                    for source in (['cloudflare','github'] if pair%2==0 else ['github','cloudflare']):
                        context=await browser.new_context(viewport={'width':1280,'height':720})
                        await context.add_init_script('''(() => {
                          const original=window.fetch.bind(window); const github='''+json.dumps(source=='github')+''';
                          window.fetch=async(input,init)=>{
                            const response=await original(input,init);
                            const url=new URL(typeof input==='string'?input:input.url,document.baseURI);
                            if(github&&url.pathname.endsWith('/startup-assets.json')){
                              const manifest=await response.clone().json();for(const m of manifest.mirrors)m.enabled=false;
                              return new Response(JSON.stringify(manifest),{status:response.status,headers:response.headers});
                            }
                            return response;
                          };
                        })();''')
                        page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                        cdp=await context.new_cdp_session(page);await cdp.send('Network.enable')
                        if mbps:await cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':120,'downloadThroughput':mbps*1e6/8,'uploadThroughput':1e6/8})
                        try:
                            for condition in ['cold','warm']:
                                start=time.monotonic()
                                if condition=='cold':await page.goto(args.url.rstrip('/')+'/play.html',wait_until='domcontentloaded',timeout=90000)
                                else:await page.reload(wait_until='domcontentloaded',timeout=90000)
                                await page.wait_for_function('window.BeforeStepGame?.state?.finite && document.querySelector("#loading").hidden && document.querySelector("#world").dataset.simulationTime',timeout=180000)
                                row={'source':source,'pair':pair+1,'mbps':mbps,'condition':condition,'seconds':time.monotonic()-start,'startup':await page.evaluate('BeforeStepGame.startup'),'page_errors':errors.copy()}
                                report['samples'].append(row);save();print(json.dumps({k:v for k,v in row.items() if k!='startup'},ensure_ascii=False),flush=True)
                                assert not errors,errors
                        finally:await context.close()
            report['passed']=True
        finally:save();await browser.close()

asyncio.run(main())

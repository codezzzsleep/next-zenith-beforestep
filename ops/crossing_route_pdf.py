"""Generate the single authorized final PDF, retaining its prior source and PDF."""
import fcntl,json,re,shutil,sys,threading
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src'),'/tmp/beforestep-pdf-deps']
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
from ops.crossing_check import Handler
from experimental.crossing.runtime import write,sha

LEDGER=ROOT/'evidence/crossing/route/pdf-addendum3.json'

if __name__=='__main__':
    with (ROOT.parent/'.memory/live/route-publication/publication.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if LEDGER.exists() and json.loads(LEDGER.read_text()).get('status')=='complete':
            print('The one final PDF exists; skipped');sys.exit(0)
        history=ROOT/'site/media/history/addendum2';history.mkdir(parents=True,exist_ok=True)
        old=json.loads((ROOT/'evidence/award/acceptance/pdf.json').read_text())
        previous=ROOT/'site/media/report.pdf';assert sha(previous)==old['sha256'],'Previous PDF differs; do not overwrite before retaining it'
        for source,name in [(previous,'report.pdf'),(ROOT/'site/project-report.html','project-report.html')]:
            target=history/name
            if not target.exists():shutil.copy2(source,target)
            assert sha(target)==sha(source)
        assert sha(history/'project-report.html')==old['pdf_source_sha256']
        write(history/'verification.json',old)
        source=ROOT/'site/report.html';source_digest=sha(source)
        state={'schema':'beforestep-final-pdf-addendum3/v1','status':'preparing','authorized_generations':1,
            'old_pdf':str((history/'report.pdf').relative_to(ROOT)),'old_pdf_sha256':old['sha256'],
            'source':'site/report.html','source_sha256':source_digest,'started_at':datetime.now(timezone.utc).isoformat()}
        temporary=ROOT/'site/media/report-addendum3-rendering.pdf'
        if not temporary.exists():
            write(LEDGER,state)
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                with sync_playwright() as p:
                    browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True)
                    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto(f'http://127.0.0.1:{server.server_port}/report.html',wait_until='networkidle',timeout=90000)
                    page.wait_for_function('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)',timeout=90000)
                    page.evaluate('document.fonts.ready');page.emulate_media(media='print')
                    state['status']='printing';write(LEDGER,state)
                    page.pdf(path=str(temporary),format='A4',print_background=True,prefer_css_page_size=True)
                    assert not errors,errors;browser.close()
            finally:server.shutdown();server.server_close()
        # Existing temporary output is validated on recovery; it is never printed twice.
        pdf=PdfReader(str(temporary));plain=''.join(page.extract_text() or '' for page in pdf.pages);compact=re.sub(r'\s+','',plain)
        phrases=['Lux3D','关键资产迭代','轮腿与想象','F1_020','F3_004','F0_003','F3_006']
        assert all(re.sub(r'\s+','',phrase) in compact for phrase in phrases)
        assert all(digest in compact for digest in old['input_sha256_values_in_pdf'])
        assert sha(source)==source_digest,'Source changed during the one PDF render; retain the generated output for reconciliation'
        temporary.replace(previous)
        state.update(status='complete',pages=len(pdf.pages),bytes=previous.stat().st_size,sha256=sha(previous),
            verified_phrases=phrases,retained_core_input_sha256=old['input_sha256_values_in_pdf'],finished_at=datetime.now(timezone.utc).isoformat())
        write(LEDGER,state)
        check=ROOT/'docs/hackathon-submission.md';text=check.read_text().replace('PDF 本轮唯一更新待 D 与追加场景终态，旧版留档',f'本轮唯一 PDF 更新已完成（{len(pdf.pages)} 页），旧版留档');check.write_text(text)
        with (ROOT.parent/'MEMORY.md').open('a') as memory:memory.write(f'\n本轮唯一PDF已生成并验证：{state["pages"]}页，site/media/report.pdf，SHA {state["sha256"]}；旧23页PDF/原project-report.html与原核验完整在site/media/history/addendum2，7核心输入SHA与失败场景文字实际从新PDF提取通过。ledger evidence/crossing/route/pdf-addendum3.json。禁止再print，后续只发布/核原字节。\n')
        print(json.dumps(state,ensure_ascii=False),flush=True)

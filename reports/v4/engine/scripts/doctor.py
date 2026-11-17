"""Read-only dependency and font check; no automatic environment mutation."""
import importlib.util,json,shutil,subprocess

def check():
    pkgs={x:bool(importlib.util.find_spec(x)) for x in ('weasyprint','numpy','PIL','fitz','tinycss2')}
    fontcmd=shutil.which('fc-list');fonts=subprocess.run([fontcmd,':lang=zh','family'],capture_output=True,text=True).stdout if fontcmd else ''
    result={'packages':pkgs,'cjk_font_found':bool(fonts.strip()),'font_detection':'fontconfig' if fontcmd else 'unavailable: visually verify Chinese glyphs','install_hint':'python3 -m pip install -r requirements.txt；Linux 另需 Pango 与 Noto CJK 字体。不要用缺字 PDF 代替正确结果。'}
    if pkgs['weasyprint']:
        try:
            from weasyprint import HTML
            result['pdf_smoke_pages']=len(HTML(string='<p>PDF 环境检查</p>').render().pages)
        except Exception as e:result['pdf_error']=str(e)
    return result

if __name__=='__main__':
    r=check();print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if all(r['packages'].values()) and r.get('pdf_smoke_pages')==1 and r.get('cjk_font_found') else 1)

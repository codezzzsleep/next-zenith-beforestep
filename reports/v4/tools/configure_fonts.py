"""Configure the report's bundled CJK fonts and a machine-local cache."""
from pathlib import Path
from xml.sax.saxutils import escape
import os
import subprocess

root = Path(__file__).resolve().parents[1]
cache = root / '.build' / 'fontconfig'
cache.mkdir(parents=True, exist_ok=True)
config = cache / 'fonts.conf'
config.write_text(f'''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
  <dir>{escape(str(root / 'fonts'))}</dir>
  <cachedir>{escape(str(cache))}</cachedir>
  <alias binding="strong"><family>Noto Sans CJK SC</family><prefer><family>BeforeStep Report Sans</family></prefer></alias>
  <alias binding="strong"><family>Noto Serif CJK SC</family><prefer><family>BeforeStep Report Serif</family></prefer></alias>
</fontconfig>
''', encoding='utf-8')
subprocess.run(['fc-cache', '-f', str(root / 'fonts')],
               env={**os.environ, 'FONTCONFIG_FILE': str(config)},
               check=True, stdout=subprocess.DEVNULL)
print(config)

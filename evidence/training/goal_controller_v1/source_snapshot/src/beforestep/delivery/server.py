"""Serve the local showcase; expose curated assets and evidence only."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from beforestep.paths import ROOT


class ShowcaseHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        url = unquote(urlsplit(path).path)
        routes = {'/assets/':ROOT/'assets','/evidence/':ROOT/'evidence',
                  '/docs/':ROOT/'docs','/submission/':ROOT/'submission'}
        for prefix, directory in routes.items():
            if url.startswith(prefix):
                candidate=(directory/url[len(prefix):]).resolve()
                if candidate.is_relative_to(directory.resolve()):return str(candidate)
                return str(ROOT/'site/_missing')
        return super().translate_path(path)


def main(argv=None):
    parser=argparse.ArgumentParser(prog='beforestep serve')
    parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8080)
    args=parser.parse_args(argv)
    handler=partial(ShowcaseHandler,directory=str(ROOT/'site'))
    with ThreadingHTTPServer((args.host,args.port),handler) as server:
        print(f'BeforeStep: http://{args.host}:{args.port}',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

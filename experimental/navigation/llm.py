"""Bounded structured-action advisor, inspired by Agentic Observer's design.

Written for this experiment; no model request occurs during import. Only a
caller-provided candidate list reaches the service. Truth is never a prompt field.
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from .world import write

ALLOWED_CONTEXT={'position','goal','known_fraction','candidates','looks_remaining','previous_outcomes'}


def validate(answer,candidates):
    if not isinstance(answer,dict) or answer.get('action') not in ('move','look','stop'):
        raise ValueError('Advisor must choose move, look or stop')
    if answer['action']=='move':
        choice=answer.get('candidate_id')
        if not isinstance(choice,int) or isinstance(choice,bool) or choice not in {c['id'] for c in candidates}:
            raise ValueError('Advisor selected an unavailable candidate')
    return {k:answer[k] for k in ('action','candidate_id','reason') if k in answer}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


class Advisor:
    def __init__(self,env_file,ledger_dir,max_calls=32):
        values={}
        if env_file:
            for line in Path(env_file).read_text().splitlines():
                if '=' in line and not line.lstrip().startswith('#'):
                    key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"').strip("'")
        self.key=values.get('NAV_LLM_API_KEY') or os.environ.get('NAV_LLM_API_KEY')
        self.base=values.get('NAV_LLM_BASE_URL') or os.environ.get('NAV_LLM_BASE_URL')
        self.model=values.get('NAV_LLM_MODEL') or os.environ.get('NAV_LLM_MODEL')
        self.directory=Path(ledger_dir);self.max_calls=max_calls;self.calls=0
        if not all((self.key,self.base,self.model)):
            raise ValueError('Set NAV_LLM_API_KEY, NAV_LLM_BASE_URL and NAV_LLM_MODEL in a private environment file')

    def choose(self,context):
        if set(context)-ALLOWED_CONTEXT:raise ValueError('Undeclared prompt fields; truth is prohibited')
        if self.calls>=self.max_calls:return {'status':'budget_exhausted'}
        snapshot=json.dumps(context,sort_keys=True,separators=(',',':'))
        identity=hashlib.sha256((self.model+snapshot).encode()).hexdigest()
        path=self.directory/(identity+'.json')
        if path.exists():return json.loads(path.read_text())
        self.calls+=1
        record={'id':identity,'status':'created','model':self.model,'context':context,'created_at_unix':time.time()}
        write(path,record)  # Durable identity precedes the external call.
        system=('You advise a lunar robot using only supplied observations. Choose one listed candidate, look, or stop. '
                'A candidate is geometrically possible in observed space; unknown space can still contain rocks. '
                'Return JSON: {"action":"move|look|stop","candidate_id":integer,"reason":"short explanation"}. '
                'Do not invent geometry, distances, candidates or observations.')
        payload={'model':self.model,'messages':[{'role':'system','content':system},{'role':'user','content':snapshot}],
                 'max_tokens':512,'temperature':0.}
        request=urllib.request.Request(self.base.rstrip('/')+'/chat/completions',
                                       data=json.dumps(payload).encode(),
                                       headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        started=time.monotonic()
        try:
            opener=urllib.request.build_opener(NoRedirect)
            with opener.open(request,timeout=45) as response:body=json.load(response)
            text=body['choices'][0]['message']['content'];start=text.find('{');end=text.rfind('}')+1
            answer=validate(json.loads(text[start:end]),context['candidates'])
            record.update(status='ok',answer=answer,usage=body.get('usage'))
        except urllib.error.HTTPError as exc:record.update(status='failed',error=f'HTTP {exc.code}')
        except Exception as exc:record.update(status='failed',error=type(exc).__name__)
        record['wall_seconds']=time.monotonic()-started;write(path,record);return record

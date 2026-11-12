"""Bounded option adjudication; every external attempt is durably recorded first."""
import hashlib,json,time,os,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from .common import write,read


def validate(answer,options):
    if not isinstance(answer,dict) or not isinstance(answer.get('option_id'),str):raise ValueError('Missing string option_id')
    if set(answer)-{'option_id','reason'}:raise ValueError('Only a listed option and reason are allowed')
    if answer['option_id'] not in {o['id'] for o in options}:raise ValueError('Unlisted option')
    reason=answer.get('reason')
    if not isinstance(reason,str) or not reason.strip():raise ValueError('Reason must be nonempty text')
    return {'option_id':answer['option_id'],'reason':reason[:600]}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


class Advisor:
    def __init__(self,env_file,ledger,max_calls=3000,stage='smoke',stage_limit=50):
        values={}
        for line in Path(env_file).read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"').strip("'")
        self.key=values.get('AI_API_key');self.base=values.get('base_URL');self.model=values.get('model')
        if not all([self.key,self.base,self.model]):raise ValueError('Missing private model configuration')
        if not urllib.parse.urlparse(self.base).path.strip('/'):self.base=self.base.rstrip('/')+'/v1'
        self.ledger=Path(ledger);self.ledger.mkdir(parents=True,exist_ok=True);self.max_calls=max_calls;self.stage=stage;self.stage_limit=stage_limit

    def choose(self,card):
        allowed={'world_id','look','targets','routes','viewpoints','options','remaining_looks','fallback_option_id'}
        if set(card)-allowed:raise ValueError('Unapproved evidence fields: no truth is permitted')
        snapshot=json.dumps(card,sort_keys=True,ensure_ascii=False);identity=hashlib.sha256((self.model+snapshot).encode()).hexdigest()
        previous=list(self.ledger.glob(identity+'-*.json'))
        if previous:
            r=read(sorted(previous)[-1]);return {**r,'wall_seconds':sum(read(p).get('wall_seconds',0.) for p in previous),'reused_record':True}
        consecutive=0
        records=[read(p) for p in self.ledger.glob('*-*.json')]
        for r in sorted(records,key=lambda r:r['created_at_unix'],reverse=True):
            if r.get('http_status') in (401,403):consecutive+=1
            else:break
        if consecutive>=5:return {'status':'service_denied','wall_seconds':0.}
        result=None;total_wait=0.
        for attempt in range(2):
            records=[read(p) for p in self.ledger.glob('*-*.json')]
            if len(records)>=self.max_calls or sum(r['stage']==self.stage for r in records)>=self.stage_limit:
                return result or {'status':'budget_exhausted','wall_seconds':0.}
            p=self.ledger/f'{identity}-{attempt}.json'
            record={'id':identity,'attempt':attempt,'status':'created','stage':self.stage,'created_at_unix':time.time(),'model':self.model,'card':card,'request_ordinal':len(records)+1}
            write(p,record)
            payload={'model':self.model,'temperature':0.,'max_tokens':8192,'response_format':{'type':'json_object'},
                     'messages':[{'role':'system','content':'Adjudicate a lunar robot decision using only the evidence card. Select exactly one supplied option_id. Unknown and permanently dark cells may contain rocks. Do not invent coordinates, geometry, or actions. Return only a JSON object with string option_id and one short reason. Keep the final answer brief.'},
                                 {'role':'user','content':snapshot}]}
            request=urllib.request.Request(self.base.rstrip('/')+'/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
            started=time.monotonic()
            try:
                with urllib.request.build_opener(NoRedirect).open(request,timeout=60) as response:
                    record['http_status']=response.status
                    body=json.load(response)
                choice=body['choices'][0];content=choice['message']['content']
                record.update(http_status=200,finish_reason=choice.get('finish_reason'),content=content,usage=body.get('usage'))
                text=content.strip();start=text.find('{');end=text.rfind('}')+1
                answer=validate(json.loads(text[start:end]),card['options']);record.update(status='ok',answer=answer)
            except urllib.error.HTTPError as exc:record.update(status='failed',http_status=exc.code,error=f'HTTP {exc.code}')
            except Exception as exc:record.update(status='failed',error=type(exc).__name__)
            record['wall_seconds']=time.monotonic()-started;write(p,record);result=record
            total_wait+=record['wall_seconds']
            if record['status']=='ok' or record.get('http_status') in (401,403):break
            # Retry only a received HTTP 200 response that failed parsing.
            # A timeout may already have reached the service: fall back without
            # submitting another attempt for that uncertain decision.
            if record.get('http_status')!=200:break
        return {**result,'wall_seconds':total_wait}


def card_and_options(evidence,goal,remaining,world_id,look):
    import numpy as np
    from beforestep.navigation import map as N
    from .policies import occupancy,viewpoints,path_risk
    from .numerical import plan
    occ=occupancy(evidence,'strict');path=plan(occ,evidence['position'],goal)
    options=[];routes=[];views=viewpoints(evidence,occ) if remaining>0 else []
    unknown=(evidence['state']==N.DARK)|(evidence['state']==N.HIDDEN)|(evidence['state']==N.UNSEEN)
    probability=np.where(unknown,.5,0.);probability[evidence['predicted_shadow']&~evidence['imagined']&unknown]=.05
    if path:
        route={'id':'go_0','kind':'go','path':path};options.append(route)
        points=np.asarray([evidence['position'],*path]);routes.append({'id':'go_0','length_m':float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),'risk':path_risk(path,evidence['position'],probability)})
    for i,v in enumerate(views):options.append({'id':f'look_{i}','kind':'look',**v})
    options.append({'id':'stop','kind':'stop','path':[]})
    fallback='go_0' if path else 'look_0' if views else 'stop'
    metrics=[{'task_id':c['task_id'],'admitted':c['admitted'],'metrics':c['metrics']} for c in evidence['candidates']]
    cover=evidence['cover'];disagreement=float(((cover>0)&(cover<max(1,len(metrics)))).sum()/max(1,(cover>0).sum()))
    card={'world_id':world_id,'look':look,'targets':[{'candidate_count':len(metrics),'admitted_count':sum(c['admitted'] for c in metrics),'candidates':metrics,'footprint_disagreement':disagreement}],
          'routes':routes,'viewpoints':[{'id':f'look_{i}','expected_new_cells':v['expected_new_cells']} for i,v in enumerate(views)],
          'options':[{'id':o['id'],'kind':o['kind']} for o in options],'remaining_looks':remaining,'fallback_option_id':fallback}
    return card,options

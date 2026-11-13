"""Render real terminal A/D recordings and mark physically unrun clips accurately."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import ROUTE,EVIDENCE

if __name__=='__main__':
    base=ROUTE/'stress_v8_gate';write(ROOT.parent/'.memory/live/post-frames.json',{'pid':os.getpid(),'status':'waiting_D'})
    while not (base/'D/result.json').exists():time.sleep(5)
    for vehicle,kind in [('A','actual'),('D','actual'),('D','rehearsal'),('D','closeup')]:
        folder=ROUTE/'handoff/frames'/f'{vehicle}-{kind}'
        if (folder/'index.json').exists() and json.loads((folder/'index.json').read_text()).get('status') in ('complete','not_applicable'):continue
        if kind=='rehearsal':available=list((base/'D/segment1').glob('rehearsal/look*/pane*/full-record/trajectory.npz'))
        elif kind=='closeup':available=[base/'D/segment2/trajectory.npz'] if (base/'D/segment2/trajectory.npz').exists() else []
        else:available=[base/vehicle/'segment1/full-record/trajectory.npz']
        if not available:
            source=base/'D/result.json';record=json.loads(source.read_text())
            write(folder/'index.json',{'status':'not_applicable','vehicle':vehicle,'kind':kind,'physics_advanced':False,
                'reason':'The actual formal first segment did not run this physical stage; no footage exists and none is fabricated',
                'formal_result_source':str(source.relative_to(ROOT)),'formal_result_sha256':sha(source),'total_result':record['total_result'],'frames':[]})
            continue
        subprocess.run([sys.executable,'ops/crossing_route_frames.py','--vehicle',vehicle,'--kind',kind],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'ops/crossing_route_models.py'],cwd=ROOT,check=True)
    write(ROOT.parent/'.memory/live/post-frames.json',{'pid':os.getpid(),'status':'complete'})

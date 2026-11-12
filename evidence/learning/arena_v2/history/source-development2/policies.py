"""Policy evidence contains observations and real hypotheses, no simulator truth."""
import numpy as np
from scipy import ndimage
from beforestep.navigation import map as N,shadows as SH
from .numerical import plan
from .geometry import solar_dark

METHODS=['conservative','optimistic','imagination','strict','strict_llm','learned','learned_no_lux','see_dark']


def evidence(state,zmax,candidates,known,position,yaw,sun,ground):
    union=np.zeros(state.shape,bool);cover=np.zeros(state.shape,np.float32);accepted=cover.copy();height=ground.copy()
    metric_maps=np.zeros((5,*state.shape),np.float32)
    padded_ground,origin=SH.terrain_grid();padded_height=padded_ground.copy()
    interior=(slice(SH.PADDING,SH.PADDING+N.NX),slice(SH.PADDING,SH.PADDING+N.NY))
    padded_height[interior]=np.maximum(padded_height[interior],zmax)
    for c in candidates:
        mask=c['mask'];cover+=mask
        for k,name in enumerate(['scale_ratio','hidden_frac','shell_contact','free_intrusion_frac','contour_iou']):
            value=c['metrics'][name];metric_maps[k]+=mask*(value if value is not None else 0)
        if c['admitted']:
            union|=mask;accepted+=mask
            # Prediction uses candidate heights, never a true scan.
            M=np.asarray(c['world_from_generated'])
            from .geometry import canonical_mesh
            import trimesh
            from .common import ROOT
            mesh=trimesh.load(ROOT/c['glb'],force='mesh',process=False);mesh.apply_transform(M)
            from .numerical import triangle_height
            predicted=triangle_height(np.asarray(mesh.vertices),np.asarray(mesh.faces),padded_ground.shape,np.asarray(origin),N.RES)
            padded_height=np.maximum(padded_height,predicted)
    metric_maps/=np.maximum(cover,1)[None]
    height=np.maximum(height,np.where(np.isfinite(zmax),zmax,ground))
    direction,tangent=SH.toward_sun()
    shadow=SH.shadow_from_height(padded_height,padded_ground[interior],direction,tangent,SH.PADDING)
    return {'state':state,'zmax':zmax,'candidates':candidates,'known_free':known,'position':np.asarray(position),
            'yaw':float(yaw),'sun':sun,'ground':ground,'imagined':union,'cover':cover,'accepted':accepted,
            'metric_maps':metric_maps,'predicted_shadow':shadow}


def occupancy(card,method,probability=None,threshold=.1):
    state=card['state'];known=card['known_free']
    if method in ('strict','strict_llm'):
        expanded=ndimage.binary_dilation(card['imagined'],iterations=1)
        return N.occupancy(state,'imagination_strict',expanded,known,predicted_shadow=card['predicted_shadow'])
    if method=='imagination':return N.occupancy(state,'imagination',ndimage.binary_dilation(card['imagined'],iterations=1),known)
    if method in ('learned','learned_no_lux'):
        occ=N.occupancy(state,'optimistic',known_free=known)
        unknown=(state==N.DARK)|(state==N.HIDDEN)|(state==N.UNSEEN)
        return occ|(unknown&~known&(probability>=threshold))
    return N.occupancy(state,'conservative' if method=='see_dark' else method,known_free=known)


def path_risk(path,start,probability):
    if not path:return None
    mask=N.swept([start,*path],r=N.R_DRIVE)
    # Dense sampling of the full swept straight segments.
    for a,b in zip([start,*path[:-1]],path):
        a,b=np.array(a),np.array(b);q=a+np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.04)))[:,None]*(b-a)
        mask|=N.swept(q,r=N.R_DRIVE)
    for p in path[:-1]:mask|=N.swept([p],r=N.R_TURN)
    values=np.asarray(probability)[mask]
    return {'max_probability':float(values.max()) if len(values) else 0.,
            'expected_occupied_cells':float(values.sum()),'swept_cells':int(mask.sum())}


def viewpoints(card,occ,limit=3):
    from beforestep.strict_pipeline import viewpoint_need
    state=card['state'];unknown=viewpoint_need(state,card['position'][0],occupied=occ)
    unknown&=(state==N.HIDDEN)|(state==N.UNSEEN)
    if not unknown.any():return []
    # Permanent DARK is excluded from expected newly measurable cells.
    focus=np.array([N.GX[unknown].mean(),N.GY[unknown].mean()]);pos=card['position'];clr=N.clearance(occ)
    candidates=[];cells=np.column_stack(np.nonzero(unknown));cells=cells[::max(1,len(cells)//160)]
    from .numerical import visible_gain
    original=N.visible_cells
    N.visible_cells=lambda state,cam,yaw,cells:visible_gain(state,np.asarray(cam),yaw,np.asarray(cells,dtype=np.int64))
    try:ranked=N.choose_second_look(state,pos,unknown,occ)
    finally:N.visible_cells=original
    for x,y,yaw,score,gain in ranked:
        xy=np.array([x,y])
        if any(np.linalg.norm(xy-p)<.25 and abs((yaw-y+np.pi)%(2*np.pi)-np.pi)<np.radians(20) for p,y in card.get('look_history',[])):continue
        if gain:candidates.append((gain,xy,yaw))
    out=[]
    for gain,xy,yaw in candidates[:40]:
        path=plan(occ,pos,xy)
        if path:out.append({'position':xy.tolist(),'yaw':yaw,'expected_new_cells':gain,'path':path})
        if len(out)>=limit:break
    # Turning at a known free pose gives a genuinely new finite view, no panorama shortcut.
    i,j=N.cell_of(*pos)
    if not out and clr[i,j]>=N.R_TURN:
        for delta in [np.pi/2,-np.pi/2,np.pi]:
            yaw=card['yaw']+delta
            if any(np.linalg.norm(pos-p)<.25 and abs((yaw-y+np.pi)%(2*np.pi)-np.pi)<np.radians(20) for p,y in card.get('look_history',[])):continue
            gain=N.visible_cells(state,pos+.42*np.array([np.cos(yaw),np.sin(yaw)]),yaw,cells)
            if gain:out.append({'position':pos.tolist(),'yaw':yaw,'expected_new_cells':gain,'path':[]})
        out.sort(key=lambda x:-x['expected_new_cells']);out=out[:limit]
    return out


def decide(card,method,goal,remaining,model=None,threshold=.1):
    probability=None
    if method.startswith('learned'):
        from .model import infer
        probability=infer(model,card,no_lux=method=='learned_no_lux')
    occ=occupancy(card,method,probability,threshold);path=plan(occ,card['position'],goal)
    if path:
        return {'kind':'go','path':path,'risk':path_risk(path,card['position'],probability) if probability is not None else None},probability,occ
    views=viewpoints(card,occ) if remaining>0 else []
    if views:return {'kind':'look',**views[0]},probability,occ
    return {'kind':'stop','path':[]},probability,occ

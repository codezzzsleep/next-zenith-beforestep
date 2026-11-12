"""CPU acceleration of the frozen cell clipping and numerical planner semantics."""
import heapq
import numpy as np
from numba import njit
from beforestep.navigation import map as N

@njit(cache=True)
def visible_gain(state,cam,yaw,cells):
    count=0
    for ix,iy in cells:
        dx=N.X0+(ix+.5)*N.RES-cam[0];dy=N.Y0+(iy+.5)*N.RES-cam[1];r=np.hypot(dx,dy)
        if r>8. or r<.3:continue
        angle=(np.degrees(np.arctan2(dy,dx)-yaw)+180)%360-180
        if abs(angle)>43.:continue
        k=int(r/(N.RES*.7));blocked=False
        for t in range(1,k):
            i=int((cam[0]+t/k*dx-N.X0)/N.RES);j=int((cam[1]+t/k*dy-N.Y0)/N.RES)
            if i<0 or i>=state.shape[0] or j<0 or j>=state.shape[1] or state[i,j]==N.ROCK:blocked=True;break
        if not blocked:count+=1
    return count

@njit(cache=True)
def triangle_height(vertices,faces,shape,origin,res):
    out=np.full(shape,-np.inf)
    for v in vertices:
        i=int(np.floor((v[0]-origin[0])/res));j=int(np.floor((v[1]-origin[1])/res))
        if 0<=i<shape[0] and 0<=j<shape[1]:out[i,j]=max(out[i,j],v[2])
    for face in faces:
        tri=vertices[face];ix=np.floor((tri[:,0]-origin[0])/res).astype(np.int64);iy=np.floor((tri[:,1]-origin[1])/res).astype(np.int64)
        if ix.min()==ix.max() and iy.min()==iy.max():continue
        for i in range(max(0,ix.min()),min(shape[0]-1,ix.max())+1):
            for j in range(max(0,iy.min()),min(shape[1]-1,iy.max())+1):
                poly=np.empty((12,3));poly[:3]=tri;n=3
                for a in range(4):
                    axis=a//2;lower=a%2==0;index=i if axis==0 else j
                    edge=origin[axis]+(index+(0 if lower else 1))*res
                    buf=np.empty((12,3));count=0
                    if n==0:break
                    prev=poly[n-1];was=prev[axis]>=edge if lower else prev[axis]<=edge
                    for k in range(n):
                        pt=poly[k];inside=pt[axis]>=edge if lower else pt[axis]<=edge
                        if inside!=was:
                            t=(edge-prev[axis])/(pt[axis]-prev[axis]);buf[count]=prev+t*(pt-prev);count+=1
                        if inside:buf[count]=pt;count+=1
                        prev=pt;was=inside
                    poly=buf;n=count
                if n>0:
                    for k in range(n):out[i,j]=max(out[i,j],poly[k,2])
    return out

@njit(cache=True)
def segment_clear(clr,a,b,x0,y0,res,radius):
    dx=b[0]-a[0];dy=b[1]-a[1];length=np.sqrt(dx*dx+dy*dy);k=max(2,int(length/.04))
    for t in range(k):
        qx=a[0]+dx*(t/(k-1));qy=a[1]+dy*(t/(k-1));i=int((qx-x0)/res);j=int((qy-y0)/res)
        if i<0 or j<0 or i>=clr.shape[0] or j>=clr.shape[1] or clr[i,j]<radius:return False
    return True

@njit(cache=True)
def graph_path(clr,nodes,x0,y0,res,radius,max_edge):
    n=len(nodes);dist=np.full(n,np.inf);prev=np.full(n,-1,np.int64);done=np.zeros(n,np.bool_);dist[0]=0.
    heap=[(0.,0)]
    while len(heap):
        d,a=heapq.heappop(heap)
        if done[a]:continue
        done[a]=True
        if a==n-1:break
        for b in range(n):
            if done[b]:continue
            dx=nodes[b,0]-nodes[a,0];dy=nodes[b,1]-nodes[a,1];length=np.sqrt(dx*dx+dy*dy)
            if length>max_edge or length<1e-6:continue
            cost=d+length+.35
            if cost<dist[b] and segment_clear(clr,nodes[a],nodes[b],x0,y0,res,radius):
                dist[b]=cost;prev[b]=a;heapq.heappush(heap,(cost,b))
    if not np.isfinite(dist[-1]):return np.empty((0,2))
    indices=[];k=n-1
    while k>0:indices.append(k);k=prev[k]
    path=np.empty((len(indices),2))
    for k in range(len(indices)):path[k]=nodes[indices[len(indices)-k-1]]
    return path


def plan(occ,start,goal):
    clr=N.clearance(occ);start=np.asarray(start,float);goal=np.asarray(goal,float)
    si,sj=N.cell_of(*start);gi,gj=N.cell_of(*goal)
    if not (0<=si<N.NX and 0<=sj<N.NY and 0<=gi<N.NX and 0<=gj<N.NY):return None
    if clr[si,sj]<N.R_DRIVE or clr[gi,gj]<N.R_DRIVE:return None
    if segment_clear(clr,start,goal,N.X0,N.Y0,N.RES,N.R_DRIVE):return [tuple(goal)]
    from scipy import ndimage
    labels,_=ndimage.label(clr>=N.R_DRIVE,structure=np.ones((3,3)))
    component=labels[si,sj]
    if not component or labels[gi,gj]!=component:return None
    xs=np.arange(N.X0+.5,N.X1-.5,.10);ys=np.arange(N.Y0+.3,N.Y1-.3,.10)
    x,y=np.meshgrid(xs,ys,indexing='ij');i=((x-N.X0)/N.RES).astype(int);j=((y-N.Y0)/N.RES).astype(int)
    good=(clr[i,j]>=N.R_TURN)&(labels[i,j]==component);nodes=np.concatenate([start[None],np.column_stack([x[good],y[good]]),goal[None]])
    path=graph_path(clr,nodes,N.X0,N.Y0,N.RES,N.R_DRIVE,2.6)
    return N.simplify(path.tolist(),start,clr) if len(path) else None

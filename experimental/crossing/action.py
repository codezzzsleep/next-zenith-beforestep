"""Analytic inverse kinematics and scripted, one-wheel-at-a-time crossing.

No pose assignment, online optimizer, or learned policy is used during motion.
The only geometry input is near/far/high on each track and crossing lateral position.
"""
import numpy as np
from .runtime import *

L1=.213;L2=.2264;SIDE=.1458699327
HIP=np.array([[.1934,-.0465,0],[.1934,.0465,0],[-.1934,-.0465,0],[-.1934,.0465,0]])

def ik(relative,leg_index):
    x,y,z=np.asarray(relative,float)-HIP[leg_index]
    a=SIDE*(-1 if leg_index in (0,2) else 1)
    z0=-np.sqrt(max(1e-9,y*y+z*z-a*a))
    hip=np.arctan2(z,y)-np.arctan2(z0,a);hip=(hip+np.pi)%(2*np.pi)-np.pi
    cosine=(x*x+z0*z0-L1*L1-L2*L2)/(2*L1*L2)
    if not (-1.0001<=cosine<=1.0001):raise ValueError('Unreachable scripted foot target')
    calf=-np.arccos(np.clip(cosine,-1,1))
    thigh=np.arctan2(-x,-z0)-np.arctan2(L2*np.sin(calf),L1+L2*np.cos(calf))
    return np.array([hip,thigh,calf])

class Script:
    def __init__(self,rec,base,feet,yaw=0):
        self.rec=rec;self.base=np.array(base,float);self.feet=np.array(feet,float);self.yaw=yaw;self.stages=[]
        self.wheel_angles=np.array([rec.e.data.qpos[rec.e.J[leg+'_wheel_joint']['qadr']]+sum(rec.e.data.qpos[rec.e.J[leg+'_'+part+'_joint']['qadr']] for part in ['thigh','calf']) for leg in LEG])
        self.rotation=np.array([[np.cos(yaw),-np.sin(yaw),0],[np.sin(yaw),np.cos(yaw),0],[0,0,1]])
    def move(self,base=None,feet=None,seconds=2,phase='shift'):
        newbase=self.base.copy() if base is None else np.array(base,float)
        newfeet=self.feet.copy() if feet is None else np.array(feet,float)
        self.stages.append({'phase':phase,'base_target':newbase.tolist(),'wheel_targets':newfeet.tolist(),'duration_s':seconds})
        seconds=max(seconds,float(np.max(np.abs(newbase-self.base)))/.035,float(np.max(np.abs(newfeet-self.feet)))/.07)
        n=int(seconds*self.rec.e.control_hz)
        for i in range(n):
            u=(i+1)/n;s=u*u*(3-2*u);b=self.base+(newbase-self.base)*s;f=self.feet+(newfeet-self.feet)*s
            actual=self.rec.e.data.qpos[:3];velocity=self.rec.e.data.qvel[:3]
            controlled_base=b+np.clip(.30*(b-actual)-.30*velocity,-.025,.025)
            rot=np.zeros(9);mujoco.mju_quat2Mat(rot,self.rec.e.data.qpos[3:7]);rot=rot.reshape(3,3)
            roll=np.arctan2(rot[2,1],rot[2,2]);pitch=np.arcsin(np.clip(-rot[2,0],-1,1))
            cr,sr=np.cos(-.5*roll),np.sin(-.5*roll);cp,sp=np.cos(-.5*pitch),np.sin(-.5*pitch)
            controlled_rotation=self.rotation@np.array([[cp,sp*sr,sp*cr],[0,cr,-sr],[-sp,cp*sr,cp*cr]])
            try:
                centres=f.copy()
                targets=np.array([ik(controlled_rotation.T@(centres[j]-controlled_base),j) for j in range(4)])
                # Grounded wheel centres use the actual rim radius projected
                # through abduction; wheel joints lie 50.37 mm inward of centres.
                for _ in range(4):
                    for j in range(4):
                        if f[j,2]<=WHEEL_R+.004:
                            centres[j,2]=WHEEL_R*np.cos(targets[j,0])+.02630213*abs(np.sin(targets[j,0]))+.001
                    targets=np.array([ik(controlled_rotation.T@(centres[j]-controlled_base),j) for j in range(4)])
            except ValueError:return False
            # Respect actual front/rear joint ranges; do not silently clamp IK.
            for j,leg in enumerate(LEG):
                for k,part in enumerate(['hip','thigh','calf']):
                    jid=mujoco.mj_name2id(self.rec.e.model,mujoco.mjtObj.mjOBJ_JOINT,leg+'_'+part+'_joint')
                    lo,hi=self.rec.e.model.jnt_range[jid]
                    if targets[j,k]<lo-.005 or targets[j,k]>hi+.005:return False
            global_angles=np.array([self.rec.e.data.qpos[self.rec.e.J[leg+'_wheel_joint']['qadr']]+sum(self.rec.e.data.qpos[self.rec.e.J[leg+'_'+part+'_joint']['qadr']] for part in ['thigh','calf']) for leg in LEG])
            omega=np.clip(10*(self.wheel_angles+(f-self.feet)@self.rotation[:,0]/WHEEL_R-global_angles),-.15/WHEEL_R,.15/WHEEL_R)
            if not self.rec.command(targets,omega,phase=phase):return False
        self.wheel_angles+=(newfeet-self.feet)@self.rotation[:,0]/WHEEL_R
        self.base=newbase;self.feet=newfeet
        for _ in range(int(self.rec.e.control_hz)):
            global_angles=np.array([self.rec.e.data.qpos[self.rec.e.J[leg+'_wheel_joint']['qadr']]+sum(self.rec.e.data.qpos[self.rec.e.J[leg+'_'+part+'_joint']['qadr']] for part in ['thigh','calf']) for leg in LEG])
            omega=np.clip(10*(self.wheel_angles-global_angles),-.15/WHEEL_R,.15/WHEEL_R)
            if not self.rec.command(targets,omega,phase=phase+'-hold'):return False
        return True
    def swing(self,j,target,height,phase):
        f=self.feet.copy();f[j,2]=height;f[j,1]=target[1]
        if not self.move(feet=f,seconds=1.5,phase=phase+'-lift'):return False
        f[j,:2]=target[:2]
        if not self.move(feet=f,seconds=max(2.,np.linalg.norm(f[j,:2]-self.feet[j,:2])/.08),phase=phase+'-swing'):return False
        f[j,2]=target[2]
        return self.move(feet=f,seconds=1.5,phase=phase+'-land')

def crossing(rec,geometry,settings=None):
    rec.leg_kd=12.
    cfg={'lift_margin_m':.035,'landing_margin_m':.025,'body_height_m':.36,'near_margin_m':.040,'support_narrow_y_m':.035}
    cfg.update(settings or {})
    near=min(geometry['near']);far=max(geometry['far']);height=max(geometry['high']);lateral=geometry.get('lateral',0.)
    # Approach is driven with normal stance; stop based on front wheel centre.
    e=rec.e;pose=stance_array(STANCE)
    if not transition(rec,pose,1.,'settle'):return False,[]
    front_line=near-WHEEL_R-cfg['near_margin_m']
    t0=e.t
    while min(wheel_positions(e)[:2,0])<front_line and e.t-t0<15:
        if not rec.command(pose,np.full(4,.07/WHEEL_R),phase='approach'):return False,[]
    feet=wheel_positions(e);base=e.data.qpos[:3].copy();sc=Script(rec,base,feet)
    # Narrow the supporting front-left wheel before the threshold. This makes
    # a support triangle near the crossing line rather than straddling its edge.
    shifted=base.copy();shifted[0]-=.04;shifted[1]=lateral-.055;shifted[2]=.32
    if not sc.move(base=shifted,seconds=3.,phase='prepare-left-support'):return False,sc.stages
    target=feet[1].copy();target[1]=lateral+cfg['support_narrow_y_m'];target[2]=WHEEL_R+.001
    if not sc.swing(1,target,WHEEL_R+.06,'narrow-left'):return False,sc.stages
    shifted=np.array([near-.13,lateral+.045,max(cfg['body_height_m'],height+.23)])
    if not sc.move(base=shifted,seconds=3.,phase='support-for-front-right'):return False,sc.stages
    landing=far+WHEEL_R+cfg['landing_margin_m'];lift=height+WHEEL_R+cfg['lift_margin_m']
    target=np.array([landing,lateral-.192,WHEEL_R+.001])
    if not sc.swing(0,target,lift,'front-right'):return False,sc.stages
    # The first crossed wheel expands support to the far side.
    shifted=np.array([near-.06,lateral-.085,max(cfg['body_height_m'],height+.23)])
    rolled=sc.feet.copy();rolled[2:,0]+=.08
    if not sc.move(base=shifted,feet=rolled,seconds=3.,phase='support-for-front-left'):return False,sc.stages
    target=np.array([landing,lateral+.192,WHEEL_R+.001])
    if not sc.swing(1,target,lift,'front-left'):return False,sc.stages
    # Translate the body over the threshold with all wheels planted/braked.
    shifted=np.array([far+.10,lateral,max(cfg['body_height_m'],height+.23)])
    rolled=sc.feet.copy();rolled[:2,0]=far+.23;rolled[2:,0]=near-WHEEL_R-cfg['near_margin_m']
    midbase=[far-.10,lateral-.10,max(cfg['body_height_m'],height+.23)]
    if not sc.move(base=midbase,feet=rolled,seconds=5.,phase='prepare-rear-support'):return False,sc.stages
    target=sc.feet[3].copy();target[1]=lateral+.06;target[2]=WHEEL_R+.001
    if not sc.swing(3,target,WHEEL_R+.06,'narrow-rear-left'):return False,sc.stages
    if not sc.move(base=shifted,seconds=4.,phase='body-over'):return False,sc.stages
    for j,side in [(2,1),(3,-1)]:
        shifted=sc.base.copy();shifted[1]=lateral+side*.055;shifted[0]=far+.12
        adjusted=sc.feet.copy()
        if j==3:
            shifted[0]=far+.11;shifted[1]=lateral-.135;shifted[2]=max(.38,height+.25);adjusted[2,0]=far+WHEEL_R+.012
        if not sc.move(base=shifted,feet=adjusted,seconds=3.,phase='support-for-'+LEG[j]):return False,sc.stages
        target=np.array([far+WHEEL_R+cfg['landing_margin_m'],lateral+(-.192 if j==2 else .192),WHEEL_R+.001])
        if not sc.swing(j,target,lift,LEG[j]):return False,sc.stages
    if not transition(rec,stance_array(STANCE_HIGH),3.,'restore-high'):return False,sc.stages
    return drive(rec,stance_array(STANCE_HIGH),far+.35,phase='depart',timeout=20),sc.stages

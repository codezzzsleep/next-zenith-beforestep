"""Analytic inverse kinematics and scripted, one-wheel-at-a-time crossing.

No pose assignment, online optimizer, or learned policy is used during motion.
The only geometry input is near/far/high on each track and crossing lateral position.
"""
import numpy as np
from .runtime import *

L1=.213;L2=.2264;SIDE=.0955
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
    """Scripted foot paths, analytic swing IK, and virtual-model stance forces."""
    def __init__(self,rec,base,feet,yaw=0):
        self.rec=rec;self.base=np.array(base,float);self.feet=np.array(feet,float)
        self.yaw=yaw;self.stages=[];self.swing_leg=None;self.near=0.;self.far=0.;self.high=0.;self.unload_fraction=1.;self.unload_loads=None;self.unloading=False;self.unload_initial_targets=None
        base_id=mujoco.mj_name2id(rec.e.model,mujoco.mjtObj.mjOBJ_BODY,'base_link')
        self.robot_mass=float(rec.e.model.body_subtreemass[base_id]);self.ground_adjust=np.zeros(4)
    def rotation(self):
        out=np.zeros(9);mujoco.mju_quat2Mat(out,self.rec.e.data.qpos[3:7]);return out.reshape(3,3)
    def stance_points(self):
        e=self.rec.e;points=wheel_positions(e).copy();points[:,2]=0.
        sums=np.zeros(4);totals=np.zeros((4,3))
        for k,c in enumerate(e.data.contact):
            a,b=int(c.geom1),int(c.geom2)
            for wheel,other in [(a,b),(b,a)]:
                if wheel in self.rec.wheel_leg and other in self.rec.ground:
                    force=np.zeros(6);mujoco.mj_contactForce(e.model,e.data,k,force)
                    j=LEG.index(self.rec.wheel_leg[wheel]);f=max(0,float(force[0]));sums[j]+=f;totals[j]+=f*c.pos
        for j in range(4):
            if sums[j]>1e-6:points[j]=totals[j]/sums[j]
        return points,sums
    def inverse_forces(self,required):
        """Closed-form floating-base force balance; no trajectory optimizer."""
        e=self.rec.e;keep=[j for j in range(4) if j!=self.swing_leg];points,loads=self.stance_points();pos=points[keep,:2]
        root=e.data.qpos[:3];rotation=self.rotation();moment=rotation@required[3:6]
        force=required[:3].copy();force[2]=float(np.clip(force[2],5,80))
        size=np.linalg.norm(force[:2])
        if size>.55*force[2]:force[:2]*=.55*force[2]/size
        height=max(.1,float(root[2]-points[keep,2].mean()))
        cop=root[:2]+np.array([-moment[1]-height*force[0],moment[0]-height*force[1]])/force[2]
        weights=np.linalg.lstsq(np.vstack([np.ones(len(keep)),pos.T]),np.r_[1.,cop],rcond=None)[0]
        weights=np.maximum(weights,.02);weights/=weights.sum()
        if self.swing_leg is not None and self.unload_fraction<1.:
            three=np.zeros(4);three[keep]=weights
            four=self.unload_loads/self.unload_loads.sum()
            weights=(1.-self.unload_fraction)*four+self.unload_fraction*three
            keep=list(range(4));pos=points[:,:2]
        centre=weights@pos
        lever=pos-centre;den=max(1e-6,float(np.sum(weights[:,None]*lever*lever)))
        yaw=moment[2]-((centre[0]-root[0])*force[1]-(centre[1]-root[1])*force[0])
        tau=required.copy()
        for k,j in enumerate(keep):
            normal=weights[k]*force[2];horizontal=weights[k]*(force[:2]+yaw*np.array([-lever[k,1],lever[k,0]])/den)
            size=np.linalg.norm(horizontal)
            if size>.55*normal:horizontal*=.55*normal/size
            jac=np.zeros((3,e.model.nv));ang=np.zeros_like(jac);bid=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_BODY,LEG[j]+'_wheel_link')
            mujoco.mj_jac(e.model,e.data,jac,ang,points[j],bid);tau-=jac.T@np.r_[horizontal,normal]
        return tau
    def move(self,base=None,feet=None,seconds=2,phase='shift'):
        newbase=self.base.copy() if base is None else np.array(base,float);newfeet=self.feet.copy() if feet is None else np.array(feet,float)
        self.stages.append({'phase':phase,'base_target':newbase.tolist(),'wheel_anchor_targets':newfeet.tolist(),'duration_s':seconds,'swing_leg':LEG[self.swing_leg] if self.swing_leg is not None else None})
        e=self.rec.e;n=int(seconds*e.control_hz);dt=1/e.control_hz;previous=None
        for i in range(n):
            u=(i+1)/n;s=u*u*(3-2*u);v=6*u*(1-u)/seconds;b=self.base+(newbase-self.base)*s;f=self.feet+(newfeet-self.feet)*s
            self.unload_fraction=s if phase.endswith('-unload') else 1.
            bv=(newbase-self.base)*v;fv=(newfeet-self.feet)*v;actual=joint_pose(e);reference=actual.copy();rotation=self.rotation()
            level=np.array([[np.cos(self.yaw),-np.sin(self.yaw),0],[np.sin(self.yaw),np.cos(self.yaw),0],[0,0,1]])
            points,loads=self.stance_points();keep=[j for j in range(4) if j!=self.swing_leg]
            weights=np.linalg.lstsq(np.vstack([np.ones(len(keep)),points[keep,:2].T]),np.r_[1.,e.data.subtree_com[1,:2]],rcond=None)[0]
            weights=np.maximum(weights,.06);weights/=weights.sum()
            for k,j in enumerate(keep):
                self.ground_adjust[j]=np.clip(self.ground_adjust[j]+dt*(.0003*min(4.,max(0.,loads[j]-1.))-.003*max(0.,1.-loads[j])),-.025,0.)
            axis_targets=f.copy()
            for j in range(4):
                posture=b.copy();posture[:2]+=np.clip(.8*(b[:2]-e.data.qpos[:2]),-.06,.06)
                is_swing=j==self.swing_leg and not self.unloading
                origin=e.data.qpos[:3] if is_swing else posture;rot=rotation if is_swing else level;point=f[j].copy();adjust=0. if is_swing else self.ground_adjust[j]
                try:
                    q=ik(rot.T@(point-origin),j)
                    for _ in range(3):
                        angle=q[0]
                        axis_z=rot[2,1]*np.cos(angle)+rot[2,2]*np.sin(angle);side=-1 if j in [0,2] else 1
                        radius=WHEEL_R*np.sqrt(max(0,1-axis_z*axis_z))+.02630213*abs(axis_z)
                        point[2]=f[j,2]+radius-side*.0503699327*axis_z-WHEEL_R+adjust
                        q=ik(rot.T@(point-origin),j)
                    reference[j]=q
                    axis_targets[j]=point
                except ValueError:
                    if j==self.swing_leg and not self.unloading:self.stages.append({'phase':'unreachable','during':phase,'leg':LEG[j],'point':point.tolist()});return False
            for j,leg in enumerate(LEG):
                for k,part in enumerate(['hip','thigh','calf']):
                    jid=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_JOINT,leg+'_'+part+'_joint');lo,hi=e.model.jnt_range[jid]
                    if j==self.swing_leg and not self.unloading and not lo-.002<=reference[j,k]<=hi+.002:
                        self.stages.append({'phase':'joint_limit','during':phase,'leg':leg,'part':part,'target':float(reference[j,k]),'range':[float(lo),float(hi)]});return False
                    reference[j,k]=np.clip(reference[j,k],lo,hi)
            ref_velocity=np.zeros((4,3)) if previous is None else np.clip((reference-previous)/dt,-2,2);previous=reference.copy()
            # Position IK supplies posture stiffness; static force balance
            # supplies only gravity compensation through the same joint PD API.
            required=e.data.qfrc_bias.copy()
            heading=np.arctan2(rotation[1,0],rotation[0,0]);yaw_rate=(rotation@e.data.qvel[3:6])[2]
            yaw_moment=float(np.clip(-6.*(heading-self.yaw)-2.*yaw_rate,-.8,.8))
            required[3:6]+=rotation.T@np.array([0.,0.,yaw_moment])
            tau=self.inverse_forces(required)
            target=reference.copy();velocity_targets=np.zeros((4,3))
            for j,leg in enumerate(LEG):
                for k,part in enumerate(['hip','thigh','calf']):
                    entry=e.J[leg+'_'+part+'_joint'];jid=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_JOINT,leg+'_'+part+'_joint');lo,hi=e.model.jnt_range[jid]
                    target[j,k]=np.clip(reference[j,k]+np.clip(tau[entry['vadr']],-10,10)/150,lo,hi)
            if phase.endswith('-unload'):
                target=(1.-s)*self.unload_initial_targets+s*target
            anchors=wheel_anchors(e);omega=[]
            for j,leg in enumerate(LEG):
                turn=sum(e.data.qvel[e.J[leg+'_'+part+'_joint']['vadr']] for part in ['thigh','calf'])+e.data.qvel[4]
                value=-turn
                if j!=self.swing_leg or self.unloading:value+=fv[j,0]/WHEEL_R+8*(f[j,0]-anchors[j,0])/WHEEL_R
                omega.append(np.clip(value,-.15/WHEEL_R,.15/WHEEL_R))
            if not self.rec.command(target,np.array(omega),phase=phase,velocity_targets=velocity_targets):return False
        self.base=newbase;self.feet=newfeet
        return True
    def balance(self,j,phase):
        margin=.16 if j==2 else .07
        for k in range(5):
            points,loads=self.stance_points();keep=[n for n in range(4) if n!=j];matrix=np.vstack([points[keep,:2].T,np.ones(3)])
            weights=np.linalg.solve(matrix,np.r_[self.rec.e.data.subtree_com[1,:2],1.])
            if np.min(weights)>=margin and np.all(loads[keep]>1e-4):return True
            safe=np.maximum(weights,margin+.02);safe/=safe.sum();delta=safe@points[keep,:2]-self.rec.e.data.subtree_com[1,:2]
            base=self.base.copy();base[:2]+=1.3*delta
            if not self.move(base=base,seconds=2.5,phase=phase+'-balance'):return False
        points,loads=self.stance_points();keep=[n for n in range(4) if n!=j];weights=np.linalg.solve(np.vstack([points[keep,:2].T,np.ones(3)]),np.r_[self.rec.e.data.subtree_com[1,:2],1.])
        if np.min(weights)<margin*.7 or not np.all(loads[keep]>1e-4):
            self.stages.append({'phase':'balance_unmet','during':phase,'weights':weights.tolist(),'loads':loads[keep].tolist()});return False
        return True
    def swing(self,j,target,height,phase):
        if not self.balance(j,phase):return False
        self.feet[j,:2]=wheel_anchors(self.rec.e)[j,:2]
        self.unload_loads=self.stance_points()[1].clip(.001)
        self.unload_initial_targets=np.array(self.rec.e._last_joint_targets).copy()
        self.swing_leg=j;self.unloading=True
        unloaded=self.feet.copy();unloaded[j,2]+=.015
        if not self.move(feet=unloaded,seconds=3.,phase=phase+'-unload'):return False
        self.unloading=False
        self.feet[j,:2]=wheel_anchors(self.rec.e)[j,:2]
        actual=joint_pose(self.rec.e)[j];rotation=self.rotation()
        axis=rotation[2,1]*np.cos(actual[0])+rotation[2,2]*np.sin(actual[0]);side=-1 if j in [0,2] else 1
        radius=WHEEL_R*np.sqrt(max(0.,1-axis*axis))+.02630213*abs(axis)
        self.feet[j,2]=wheel_anchors(self.rec.e)[j,2]-radius+side*.0503699327*axis+WHEEL_R
        f=self.feet.copy();f[j,2]=height;b=self.base.copy()
        if phase=='RL':b[0]=self.far+.22+max(0.,self.high-.12)*2/3;b[2]=max(.38,self.high+.27);f[j,1]=target[1]
        elif phase!='RR':f[j,1]=target[1]
        if not self.move(base=b,feet=f,seconds=4. if phase=='RL' else 2.5,phase=phase+'-lift'):return False
        f[j,:2]=target[:2]
        b=self.base.copy()
        if phase=='front-right':b[0]-=.015*(target[0]-self.feet[j,0]);b[2]-=.005
        if not self.move(base=b,feet=f,seconds=max(2.,np.linalg.norm(f[j,:2]-self.feet[j,:2])/.08),phase=phase+'-swing'):return False
        if phase=='front-right':
            b=self.base.copy()
            if not self.move(base=b,seconds=2.,phase='align-before-first-landing'):return False
        if phase=='front-left':
            b=self.base.copy();b[0]=self.near;b[1]=self.lateral-.025;b[2]=max(.38,self.high+.26);other=f.copy();other[0,0]=self.far+.25;other[2:,0]=self.near-.24
            if not self.move(base=b,feet=other,seconds=8.,phase='centre-before-front-left-landing'):return False
            f=other
        if phase=='RR':
            b=self.base.copy();b[0]=self.far+.13;b[2]=max(.39,self.high+.28);ground=self.feet.copy();ground[3,0]=self.near-.10;ground[j,2]=target[2]+.05
            if not self.move(base=b,feet=ground,seconds=4.,phase='centre-before-third-landing'):return False
            f=ground
        if phase=='RL':
            b=self.base.copy();b[0]=self.far+.20;b[1]=self.lateral+.04
            clear=self.feet.copy();clear[:2,0]=self.far+.32
            if not self.move(base=b,feet=clear,seconds=4.,phase='centre-before-last-landing'):return False
            f=clear
        f[j,2]=target[2]-.003
        if not self.move(feet=f,seconds=4.,phase=phase+'-land'):return False
        self.swing_leg=None
        if not self.move(seconds=.5,phase=phase+'-seat'):return False
        return True

def crossing(rec,geometry,settings=None):
    cfg={'lift_margin_m':.035,'landing_margin_m':.055,'rear_landing_margin_m':.025,'body_height_m':.38,'near_margin_m':.040,'support_narrow_y_m':-.015}
    cfg.update(settings or {});rec.leg_kd=5.
    near=min(geometry['near']);far=max(geometry['far']);height=max(geometry['high']);lateral=geometry.get('lateral',0.)
    # Approach is driven with normal stance; stop based on front wheel centre.
    e=rec.e;pose=stance_array(STANCE)
    if not transition(rec,pose,1.,'settle'):return False,[]
    front_line=near-WHEEL_R-cfg['near_margin_m']
    t0=e.t
    while min(wheel_anchors(e)[:2,0])<front_line and e.t-t0<15:
        if not rec.command(pose,np.full(4,.07/WHEEL_R),phase='approach'):return False,[]
    # Physically align on four grounded wheels. Integral feedback overcomes
    # static wheel/skid friction without changing the common wheel speed cap.
    align_start=e.t;integral=0.
    while e.t-align_start<30.:
        w,x,y,z=e.data.qpos[3:7];yaw=np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
        if abs(yaw)<.003:break
        integral=np.clip(integral+yaw/e.control_hz,-.5,.5)
        speed=float(np.clip(-1.5*yaw-.5*integral,-.15,.15))
        omega=np.array([(1 if leg in ['FR','RR'] else -1)*speed/WHEEL_R for leg in LEG])
        if not rec.command(pose,omega,phase='align-heading-on-four-wheels'):return False,[]
    for _ in range(int(.5*e.control_hz)):
        if not rec.command(pose,phase='seat-after-heading-alignment'):return False,[]
    feet=wheel_anchors(e);base=e.data.qpos[:3].copy();sc=Script(rec,base,feet);sc.near=near;sc.far=far;sc.high=height;sc.lateral=lateral
    # Narrow the supporting front-left wheel before the threshold. This makes
    # a support triangle near the crossing line rather than straddling its edge.
    shifted=base.copy();shifted[0]-=.04;shifted[1]=lateral-.055;shifted[2]=.32
    if not sc.move(base=shifted,seconds=3.,phase='prepare-left-support'):return False,sc.stages
    target=feet[1].copy();target[0]=near-.10;target[1]=lateral+cfg['support_narrow_y_m'];target[2]=WHEEL_R+.001
    if not sc.swing(1,target,WHEEL_R+.06,'narrow-left'):return False,sc.stages
    shifted=np.array([near-.33,lateral+.02,max(cfg['body_height_m'],height+.27)])
    rolled=sc.feet.copy();rolled[2:,0]=near-.43
    if not sc.move(base=shifted,feet=rolled,seconds=5.,phase='raise-and-centre'):return False,sc.stages
    shifted[0]=near-.12;rolled[2:,0]=near-.33
    if not sc.move(base=shifted,feet=rolled,seconds=8.,phase='support-for-front-right'):return False,sc.stages
    landing=far+WHEEL_R+cfg['landing_margin_m'];lift=height+WHEEL_R+cfg['lift_margin_m']
    target=np.array([landing,lateral-.10,WHEEL_R+.001])
    if not sc.swing(0,target,lift,'front-right'):return False,sc.stages
    # The first crossed wheel expands support to the far side.
    shifted=np.array([near-.06,lateral-.085,max(.38,height+.26)])
    rolled=sc.feet.copy()
    if not sc.move(base=shifted,feet=rolled,seconds=3.,phase='support-for-front-left'):return False,sc.stages
    target=np.array([landing,lateral+.142,WHEEL_R+.001])
    if not sc.swing(1,target,lift,'front-left'):return False,sc.stages
    # Translate the body over the threshold with all wheels planted/braked.
    shifted=np.array([far+.10,lateral,max(.38,height+.26)])
    rolled=sc.feet.copy();rolled[:2,0]=far+.23;rolled[2:,0]=near-WHEEL_R-cfg['near_margin_m']
    midbase=[far-.10,lateral-.025,max(.38,height+.26)]
    if not sc.move(base=midbase,feet=rolled,seconds=5.,phase='prepare-rear-support'):return False,sc.stages
    target=sc.feet[3].copy();target[1]=lateral-.04;target[2]=WHEEL_R+.001
    if not sc.swing(3,target,WHEEL_R+.06,'narrow-rear-left'):return False,sc.stages
    if not sc.move(base=shifted,seconds=4.,phase='body-over'):return False,sc.stages
    for j,side in [(2,1),(3,-1)]:
        shifted=sc.base.copy();shifted[1]=lateral+side*.025;shifted[0]=far+.10;shifted[2]=max(.405,height+.285)
        adjusted=sc.feet.copy()
        if j==3:
            shifted[0]=far+.17;shifted[1]=lateral;shifted[2]=max(.38,height+.275);adjusted[:2,0]=far+.29;adjusted[2,0]=far+WHEEL_R+cfg['rear_landing_margin_m'];adjusted[3,0]=near-.10
        if not sc.move(base=shifted,feet=adjusted,seconds=3.,phase='support-for-'+LEG[j]):return False,sc.stages
        target=np.array([far+WHEEL_R+cfg['rear_landing_margin_m'],lateral+(.015 if j==2 else .142),WHEEL_R+.001])
        if not sc.swing(j,target,lift,LEG[j]):return False,sc.stages
    depart_feet=sc.feet.copy();depart_feet[:2,0]=far+.60;depart_feet[2:,0]=far+.20;depart_feet[:,1]=[lateral-.142,lateral+.142,lateral-.142,lateral+.142]
    if not sc.move(base=[far+.39,lateral,.46],feet=depart_feet,seconds=7.,phase='restore-wheelbase'):return False,sc.stages
    if not transition(rec,stance_array(STANCE_HIGH),3.,'restore-high'):return False,sc.stages
    return drive(rec,stance_array(STANCE_HIGH),far+.35,phase='depart',timeout=20),sc.stages

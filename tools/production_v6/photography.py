"""Camera-only presentation choices; original joints and collision geometry stay fixed."""
import xml.etree.ElementTree as ET
from pathlib import Path
import mujoco

from common import ROOT

def original_actor(vm):
    xml=ET.parse(ROOT/'vendor/unitree_mujoco/unitree_robots/go2w/go2w.xml').getroot()
    materials={g.get('mesh'):g.get('material') for g in xml.iter('geom') if g.get('mesh')}
    changed=[]
    for gi in range(vm.m.ngeom):
        name=mujoco.mj_id2name(vm.m,mujoco.mjtObj.mjOBJ_GEOM,gi) or ''
        if name.startswith('vid_'):
            vm.m.geom_group[gi]=3
            continue
        if vm.m.geom_type[gi]!=mujoco.mjtGeom.mjGEOM_MESH:continue
        mesh=mujoco.mj_id2name(vm.m,mujoco.mjtObj.mjOBJ_MESH,int(vm.m.geom_dataid[gi]))
        if mesh not in materials:continue
        vm.m.geom_group[gi]=2
        vm.m.geom_rgba[gi]=[1,1,1,1]
        mat=materials[mesh]
        if mat:
            vm.m.geom_matid[gi]=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_MATERIAL,mat)
        else:
            vm.m.geom_matid[gi]=-1
            vm.m.geom_rgba[gi]=[.11,.12,.13,1]
        changed.append(mesh)
    return sorted(set(changed))

def quality(vm,exposure=False):
    vm.m.vis.quality.shadowsize=4096
    vm.m.vis.quality.offsamples=4
    if exposure:
        lid=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_LIGHT,'v7_sun')
        vm.m.light_diffuse[lid]=[.9,.9*.985,.9*.95]
        vm.m.light_ambient[lid]=[.06,.06,.066]
        vm.m.light_specular[lid]=[.08,.08,.08]
        vm.m.vis.headlight.ambient=[.12,.12,.13]
        vm.m.vis.headlight.diffuse=[.08,.08,.08]
        vm.m.vis.headlight.specular=[0,0,0]

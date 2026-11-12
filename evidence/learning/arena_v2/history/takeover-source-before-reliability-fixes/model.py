"""Convolutional privileged-teacher imitation of hidden occupancy, not route search."""
import numpy as np
import torch
from torch import nn
from beforestep.navigation import map as N

CHANNELS=22
LUX_CHANNELS=slice(6,15)


def features(card,no_lux=False):
    state=card['state'];position=card['position'];dx=N.GX-position[0];dy=N.GY-position[1]
    distance=np.hypot(dx,dy);yaw=card['yaw'];az=np.radians(card['sun']['azimuth_deg'])
    channels=[*(state==k for k in range(6)),np.minimum(card['cover']/12,1),np.minimum(card['accepted']/12,1),card['predicted_shadow'],
              *card['metric_maps'],np.divide(card['cover']-card['accepted'],np.maximum(card['cover'],1)),
              np.full(state.shape,np.cos(yaw)),np.full(state.shape,np.sin(yaw)),
              np.full(state.shape,-np.cos(az)),np.full(state.shape,np.sin(az)),np.minimum(distance/14,1),
              np.clip(np.nan_to_num(card['zmax'],neginf=0)/1.5,0,1),card['known_free']]
    x=np.asarray(channels,np.float32)
    if no_lux:x[LUX_CHANNELS]=0
    assert x.shape==(CHANNELS,N.NX,N.NY)
    return x


class HiddenOccupancy(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc=nn.Sequential(nn.Conv2d(CHANNELS,16,5,padding=2),nn.ReLU(),nn.Conv2d(16,24,3,stride=2,padding=1),nn.ReLU(),
                              nn.Conv2d(24,32,3,stride=2,padding=1),nn.ReLU())
        self.context=nn.Sequential(nn.Conv2d(32,32,3,padding=2,dilation=2),nn.ReLU(),
                                   nn.Conv2d(32,32,3,padding=4,dilation=4),nn.ReLU(),nn.Conv2d(32,24,3,padding=8,dilation=8),nn.ReLU())
        self.head=nn.Sequential(nn.Conv2d(24+CHANNELS,16,3,padding=1),nn.ReLU(),nn.Conv2d(16,1,1))

    def forward(self,x):
        context=self.context(self.enc(x));context=nn.functional.interpolate(context,size=x.shape[-2:],mode='bilinear',align_corners=False)
        return self.head(torch.cat([x,context],1))[:,0]


def infer(model,card,no_lux=False):
    # Accepts only a policy evidence card; no World or teacher occupancy can enter.
    model.eval()
    with torch.inference_mode():probability=torch.sigmoid(model(torch.from_numpy(features(card,no_lux))[None]))[0].numpy()
    state=card['state'];probability[(state==N.FREE)|card['known_free'].astype(bool)]=0.
    probability[(state==N.ROCK)|(state==N.NOGO)]=1.
    return probability


def load(path):
    data=torch.load(path,map_location='cpu',weights_only=False);model=HiddenOccupancy();model.load_state_dict(data['state_dict']);return model

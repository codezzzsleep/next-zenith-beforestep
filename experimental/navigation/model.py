"""Learned traversability encoder and differentiable value-iteration actor.

The actor emits eight direction scores. It does not call the offline Dijkstra
teacher. Fixed neighbor topology and a common observed-obstacle guard are
declared inductive biases, rather than a claim of rule-free robot software.
"""
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from .world import DIRECTIONS


def neighbors(value):
    padded = F.pad(value,(1,1,1,1),value=0.)
    n,m = value.shape[-2:]
    return torch.stack([padded[:,1+int(dx):1+int(dx)+n,1+int(dy):1+int(dy)+m]
                        for dx,dy in DIRECTIONS],1)


class NavigationNet(nn.Module):
    def __init__(self, iterations=48):
        super().__init__()
        self.iterations = iterations
        self.encoder = nn.Sequential(nn.Conv2d(4,24,5,padding=2),nn.ReLU(),
                                     nn.Conv2d(24,24,3,padding=1),nn.ReLU(),
                                     nn.Conv2d(24,16,3,padding=1),nn.ReLU(),
                                     nn.Conv2d(16,1,1))
        self.log_cost = nn.Parameter(torch.tensor(-5.))
        self.log_penalty = nn.Parameter(torch.tensor(-1.))
        self.discount_logit = nn.Parameter(torch.tensor(4.))
        self.direction_bias = nn.Parameter(torch.zeros(8))

    def forward(self, inputs, goal):
        blocked_logits = self.encoder(inputs).squeeze(1)
        blocked = torch.sigmoid(blocked_logits)
        cost = F.softplus(self.log_cost) + F.softplus(self.log_penalty)*blocked
        lengths = torch.tensor(np.linalg.norm(DIRECTIONS,axis=1),device=inputs.device,dtype=inputs.dtype)
        discount = torch.sigmoid(self.discount_logit)
        value = goal.clone()
        adjacent = neighbors(cost)
        transitions = []
        # Penalize diagonal corner cuts through the two predicted adjacent cells.
        for a,(dx,dy) in enumerate(DIRECTIONS):
            if dx and dy:
                ia = next(i for i,d in enumerate(DIRECTIONS) if tuple(d)==(dx,0))
                ib = next(i for i,d in enumerate(DIRECTIONS) if tuple(d)==(0,dy))
                transitions.append(torch.maximum(adjacent[:,a],torch.maximum(adjacent[:,ia],adjacent[:,ib])))
            else:
                transitions.append(adjacent[:,a])
        transition = torch.stack(transitions,1)
        for _ in range(self.iterations):
            q = discount*neighbors(value)-transition*lengths[None,:,None,None]
            q = q+self.direction_bias[None,:,None,None]*.005
            value = torch.maximum(goal,q.max(1).values)
        return q,blocked_logits


def load_model(path, iterations):
    model = NavigationNet(iterations)
    checkpoint = torch.load(path,map_location='cpu',weights_only=True)
    model.load_state_dict(checkpoint['model'])
    model.eval()
    return model


def infer(model, features, goal):
    marker = np.zeros(features.shape[1:],np.float32)
    marker[tuple(goal)] = 1.
    with torch.no_grad():
        q,blocked = model(torch.from_numpy(features[None]),torch.from_numpy(marker[None]))
    return q[0].numpy(),torch.sigmoid(blocked[0]).numpy()

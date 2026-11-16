/** Presentation pacing is independent of collision and rehearsal certification. */
export class MissionShowcase {
  constructor(enabled=false,checkpointX=2.85){this.enabled=enabled;this.checkpointX=checkpointX;this.stage=enabled?'approach':'free';this.active=false;this.completed=false;this.viewedTask=null;this.releaseMode=null;this.triggers=0;}
  get locked(){return this.enabled&&this.active&&!this.completed;}
  trigger(x){if(!this.enabled||this.completed||this.active||x<this.checkpointX)return false;this.active=true;this.stage='braking';this.viewedTask=null;this.triggers++;return true;}
  stopped(){if(this.stage!=='braking')return false;this.stage=this.viewedTask?'model-seen':'observe';return true;}
  view(task,selected){if(!this.enabled)return true;if(!selected.includes(task))return false;this.viewedTask=task;if(this.active&&this.stage!=='braking')this.stage='model-seen';return true;}
  canContinue(selected){return !this.enabled||this.completed||this.active&&this.stage==='model-seen'&&!!this.viewedTask&&selected.includes(this.viewedTask);}
  release(mode,selected){if(!this.canContinue(selected))return false;this.active=false;this.completed=true;this.releaseMode=mode;this.stage='high-rocks';return true;}
  selectionChanged(selected){if(this.completed)return;if(this.viewedTask&&!selected.includes(this.viewedTask)){this.viewedTask=null;if(this.active&&this.stage!=='braking')this.stage='observe';}}
  state(){return {enabled:this.enabled,checkpointX:this.checkpointX,stage:this.stage,active:this.active,completed:this.completed,viewedTask:this.viewedTask,releaseMode:this.releaseMode,triggers:this.triggers};}
}

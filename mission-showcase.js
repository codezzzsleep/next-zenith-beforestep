/** Presentation pacing is independent of collision and rehearsal certification. */
export class MissionShowcase {
  constructor(enabled=false,checkpointX=2.85){this.enabled=enabled;this.checkpointX=checkpointX;this.stage=enabled?'approach':'free';this.active=false;this.completed=false;this.viewedTask=null;this.releaseMode=null;this.triggers=0;this.initialJudgment=null;}
  get locked(){return this.enabled&&this.active&&!this.completed;}
  trigger(x){if(!this.enabled||this.completed||this.active||x<this.checkpointX)return false;this.active=true;this.stage='braking';this.viewedTask=null;this.triggers++;return true;}
  stopped(){if(this.stage!=='braking')return false;this.stage='observe';return true;}
  judge(choice){if(!this.active||this.stage==='braking'||this.initialJudgment||!['pass','detour','unsure'].includes(choice))return false;this.initialJudgment=choice;this.stage='decision';return true;}
  view(task,selected){if(!this.enabled)return true;if(!selected.includes(task))return false;this.viewedTask=task;return true;}
  canContinue(){return !this.enabled||this.completed||this.active&&this.stage!=='braking'&&!!this.initialJudgment;}
  release(mode,selected){if(!this.canContinue(selected))return false;this.active=false;this.completed=true;this.releaseMode=mode;this.stage='high-rocks';return true;}
  selectionChanged(selected){if(this.viewedTask&&!selected.includes(this.viewedTask))this.viewedTask=null;}
  state(){return {enabled:this.enabled,checkpointX:this.checkpointX,stage:this.stage,active:this.active,completed:this.completed,viewedTask:this.viewedTask,releaseMode:this.releaseMode,triggers:this.triggers,initialJudgment:this.initialJudgment};}
}

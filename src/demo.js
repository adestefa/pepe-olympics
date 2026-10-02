/** Emits the same key edges used by the player, paced by simulation time. */
export class VaultDemo {
  constructor(){this.reset();}
  reset(){this.active=false;this.age=0;this.lastStep=-1;this.nextFoot='KeyD';this.held=new Set();this.stage='';this.stageAge=0;this.caption='';}
  start(){this.reset();this.active=true;this.caption='Watch the keys: hold Space, time J, tap K.';}
  update(dt,s){
    if(!this.active)return [];
    this.age+=dt;const stage=s.phase;
    if(stage!==this.stage){this.stage=stage;this.stageAge=0;}else this.stageAge+=dt;
    const want=new Set(),taps=[];
    if(stage==='run'){
      this.caption=s.x<-19?'TAP D, then L · steady half-second steps':'HOLD H briefly · lower the pole quickly';
      if(this.age-this.lastStep>=.44*95/(s.weightKg??95)){taps.push(this.nextFoot);this.nextFoot=this.nextFoot==='KeyD'?'KeyL':'KeyD';this.lastStep=this.age;}
      if(s.x>=-19&&s.frame<49)want.add('KeyH');
      if(s.x>=-12){want.add('Space');this.caption='HOLD SPACE · plant and store spring power';}
    }else if(stage==='vault'){
      const m=s.momentum;
      if(m.chargeSeconds<.35)want.add('Space');
      if(!m.swingUsed){
        this.caption=m.age<.35?'HOLD SPACE · charging as the body moves forward':'WAIT for the surge · watch J turn green';
        if(m.swingWindow>.93&&s.frame>=121)want.add('KeyJ');
      }else if(!m.throwUsed){
        this.caption=s.frame<165?'HOLD J · swing the feet up with the momentum':'TAP K · throw as the swing peaks';
        if(s.frame<169)want.add('KeyJ');
        if(s.frame>=165&&m.throwWindow>.94)taps.push('KeyK');
      }else this.caption='K commits the throw · more Space would launch higher';
    }
    else if(stage==='flight')this.caption='Keys released · gravity takes over';
    else if(stage==='landed')this.caption='Your turn · copy the timing, or tap faster for chaos';
    else if(stage==='crash')this.caption='Mistakes become a ragdoll · R resets the round';
    const events=[];
    for(const key of this.held)if(!want.has(key))events.push({key,down:false});
    for(const key of want)if(!this.held.has(key))events.push({key,down:true});
    for(const key of taps)events.push({key,down:true},{key,down:false});
    this.held=want;return events;
  }
  suspend(){this.held.clear();}
}

const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export class VaultPhases {
  constructor(){this.reset();}
  reset(){this.frame=1;this.state='approach';this.plantRate=145;this.message='D / L TO STEP · H TO LOWER POLE';}
  lowerPoleTap(){if(this.state==='approach')this.frame=clamp(this.frame+12,1,49);}
  plant(rate=145){if(this.state!=='approach')return false;this.plantRate=rate;this.state='plant';return true;}
  throw(){if(!['loaded','swing'].includes(this.state)||this.frame<165)return false;this.state='throw';return true;}
  release(){if(!['plant','loaded','swing','throw','inverted'].includes(this.state))return false;this.state='released';return true;}
  update(dt,{raise=false,swing=false}={}){
    if(this.state==='approach')this.frame=clamp(this.frame+dt*(raise?112:0),1,49);
    else if(this.state==='plant'){
      this.frame=Math.min(121,this.frame+dt*this.plantRate);
      if(this.frame>=121)this.state='loaded';
    }else if(['loaded','swing'].includes(this.state)&&swing){
      this.frame=Math.min(169,this.frame+dt*92);this.state='swing';
    }else if(this.state==='throw'){
      this.frame=Math.min(193,this.frame+dt*94);if(this.frame>=193)this.state='inverted';
    }
    this.message=this.state==='approach'?'D / L TO STEP · H TO LOWER POLE':this.state==='plant'?'MOMENTUM IS CARRYING YOU · HOLD SPACE TO CHARGE':this.frame<165?'TIME J WITH THE SURGE · HOLD TO SWING':this.frame<193?'TAP K · TURN MOMENTUM INTO A THROW':'LET IT FLY';
    return this.frame;
  }
}

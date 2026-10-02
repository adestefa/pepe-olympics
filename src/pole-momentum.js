const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const bell=(time,target,width)=>clamp(1-Math.abs(time-target)/width,0,1);

/** One angular degree of freedom about the planted tip, in meters/seconds/radians.
 * Limb poses follow this arc; the final velocity is handed to the ragdoll.
 */
export class PoleMomentum {
  constructor(){this.reset();}
  reset(){
    this.active=false;this.age=0;this.angle=0;this.angularVelocity=0;this.chargeSeconds=0;
    this.charge=0;this.swingUsed=false;this.swingTiming=0;this.throwTiming=0;
    this.throwUsed=false;this.swingAt=null;this.swingTarget=0;this.feedback='';this.failed=false;
  }
  plant(speed,quality,loadingTime,weightKg=95){
    this.reset();this.active=true;this.speed=speed;this.quality=quality;this.massRatio=weightKg/95;
    this.angularVelocity=.23+speed*.035;
    this.swingTarget=loadingTime+.23;
  }
  get swingWindow(){return !this.active||this.swingUsed?0:bell(this.age,this.swingTarget,.34);}
  get throwWindow(){return this.swingAt===null||this.throwUsed?0:bell(this.age,this.swingAt+.62,.40);}
  swing(frame){
    if(!this.active||this.swingUsed)return false;
    this.swingUsed=true;this.swingAt=this.age;
    this.swingTiming=frame>=112?this.swingWindowScore():0;
    // One impulse per attempt. Holding or spamming J cannot farm energy.
    this.angularVelocity+=(.035+.38*this.swingTiming)*(.7+this.speed*.035)/this.massRatio;
    this.feedback=this.swingTiming>.72?'PERFECT SWING · MOMENTUM BOOST':this.age<this.swingTarget?'EARLY SWING · SMALL BOOST':'LATE SWING · MISSED THE SURGE';
    return true;
  }
  swingWindowScore(){return bell(this.age,this.swingTarget,.34);}
  throw(frame){
    if(!this.active||this.throwUsed)return false;
    if(!this.swingUsed||frame<165){this.feedback='TOO EARLY · SWING WITH J, THEN TAP K';return false;}
    this.throwTiming=this.throwWindow;this.throwUsed=true;
    this.feedback=this.throwTiming>.7?'GOOD THROW · LET IT FLY':'OFF-BEAT THROW · HANG ON';
    return true;
  }
  update(dt,{charge=false}={}){
    if(!this.active)return;
    this.age+=dt;
    if(charge)this.chargeSeconds=Math.min(2,this.chargeSeconds+dt);
    this.charge=this.chargeSeconds/2;
    // Run-up momentum loads the pole, gravity slows the rising arc, and drag
    // dissipates energy. Space stores extra spring energy for the K throw.
    const spring=(.42+this.speed*.018)*Math.exp(-this.age/.42)/this.massRatio;
    const acceleration=spring-.68*Math.sin(this.angle)-.16*this.angularVelocity;
    this.angularVelocity+=acceleration*dt;
    this.angle+=this.angularVelocity*dt;
    this.failed=this.age>3.6||this.angle>2.2||(this.age>1.5&&this.angularVelocity<-.12);
  }
  snapshot(){return {active:this.active,age:this.age,angle:this.angle,angularVelocity:this.angularVelocity,charge:this.charge,chargeSeconds:this.chargeSeconds,swingUsed:this.swingUsed,swingTiming:this.swingTiming,throwUsed:this.throwUsed,throwTiming:this.throwTiming,swingWindow:this.swingWindow,throwWindow:this.throwWindow,swingTarget:this.swingTarget,feedback:this.feedback,failed:this.failed};}
}

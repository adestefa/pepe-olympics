import * as C from 'cannon-es';

export const JOINTS = [
  ['hips',null,[0,1.24,0],[.33,.16,.21],[0,-.02,0],8],
  ['chest','hips',[0,.34,0],[.48,.34,.22],[0,.20,0],12],
  ['head','chest',[0,.69,0],[.4,.44,.29],[0,.22,.035],4],
  ...['left','right'].flatMap((s,i)=> {const sign=i?1:-1;return [
    [s+'UpperLeg','hips',[sign*.235,-.03,0],[.18,.28,.18],[0,-.28,0],4],
    [s+'LowerLeg',s+'UpperLeg',[0,-.61,0],[.12,.25,.14],[0,-.23,.045],2.8],
    [s+'UpperArm','chest',[sign*.53,.44,.20],[.17,.23,.17],[sign*.025,-.22,0],2.2],
    [s+'LowerArm',s+'UpperArm',[sign*.025,-.45,0],[.11,.21,.11],[0,-.19,0],1.4],
    [s+'Hand',s+'LowerArm',[sign*.025,-.40,0],[.10,.105,.085],[0,-.04,0],.5]
  ];})
 ];
// The source model faces +Z. In the arena, forward is +X: rotate the whole anatomical frame.
for(const spec of JOINTS){for(const idx of [2,4]){const [x,y,z]=spec[idx];spec[idx]=[z,y,-x];}const [x,y,z]=spec[3];spec[3]=[z,y,x];}
const V=(x=0,y=0,z=0)=>new C.Vec3(x,y,z);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function angle(body){const q=body.quaternion;return Math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));}
function wrap(v){return Math.atan2(Math.sin(v),Math.cos(v));}

export class VaultPhysics {
  constructor(){
    this.world=new C.World({gravity:V(0,-9.81,0)});this.world.solver.iterations=24;this.world.allowSleep=false;
    this.world.defaultContactMaterial.friction=.45;this.world.defaultContactMaterial.restitution=.07;
    this.ground=new C.Body({mass:0,shape:new C.Plane(),collisionFilterGroup:1});this.ground.quaternion.setFromEuler(-Math.PI/2,0,0);this.world.addBody(this.ground);
    this.mat=new C.Material('landing-pad');this.world.addContactMaterial(new C.ContactMaterial(this.mat,this.mat,{friction:.65,restitution:.02}));
    this.pad=new C.Body({mass:0,shape:new C.Box(V(3.6,.37,2.5)),position:V(6.5,.37,0),material:this.mat,collisionFilterGroup:1});this.world.addBody(this.pad);
    this.staticBodies=[this.ground,this.pad];this.height=4.2;this.reset(-3.9,'preview');
  }
  reset(x=-14,mode='ready'){
    for(const c of [...this.world.constraints])this.world.removeConstraint(c);
    for(const b of [...this.world.bodies])if(!this.staticBodies.includes(b))this.world.removeBody(b);
    this.accumulator=0;this.bodies={};this.joints={};this.time=0;this.runDrive=0;this.poleLift=0;this.balanceAssist=1;this.lastFoot=null;this.lastStepTime=-10;this.footTimes={left:-10,right:-10};this.cadence='TAP D, THEN L';this.phase=mode;this.phaseTime=0;this.maxHeight=0;this.barHit=false;this.peakImpact=0;this.pole=[];this.poleJoints=[];this.grips=[];this.vaultTime=0;this.result=null;this.tucked=false;this.breakName=null;this.launchQuality=0;this.passed=false;this.overBar=false;this.crossingChecked=false;
    for(const [name,parent,offset,size,center,mass] of JOINTS){
      const pos=parent?this.bodies[parent].position.vadd(V(...offset)):V(x,offset[1],0);
      const body=new C.Body({mass,position:pos,linearDamping:.12,angularDamping:.5,collisionFilterGroup:2,collisionFilterMask:1|4});
      body.addShape(new C.Box(V(...size)),V(...center));body.name=name;body.restZ=pos.z;body.material=this.mat;this.world.addBody(body);this.bodies[name]=body;
      body.addEventListener('collide',e=>{if(e.body===this.bar){this.barHit=true;this.dropBar();}if(e.body===this.ground||e.body===this.pad){const impact=Math.abs(e.contact.getImpactVelocityAlongNormal());this.peakImpact=Math.max(this.peakImpact,impact);if(['flight','crash'].includes(this.phase)&&this.phaseTime>.25&&['head','chest','hips'].includes(name)){this.landingSurface=e.body===this.pad?'pad':'track';this.land();}}});
      if(parent){const ball=name.endsWith('UpperArm');const hinge=ball?new C.ConeTwistConstraint(this.bodies[parent],body,{pivotA:V(...offset),pivotB:V(),axisA:V(0,-1,0),axisB:V(0,-1,0),angle:2.5,twistAngle:Math.PI,collideConnected:false,maxForce:2e4}):new C.HingeConstraint(this.bodies[parent],body,{pivotA:V(...offset),pivotB:V(),axisA:V(0,0,1),axisB:V(0,0,1),collideConnected:false,maxForce:2e4});if(!ball){hinge.enableMotor();hinge.setMotorMaxForce(110);}this.world.addConstraint(hinge);this.joints[name]={hinge,parent,body,target:0,ball,targetQ:new C.Quaternion()};}
    }
    this.createPole(x);
    this.bar=new C.Body({mass:.8,shape:new C.Box(V(.045,.045,2.05)),position:V(2.3,this.height,0),type:C.Body.STATIC,collisionFilterGroup:4,collisionFilterMask:1|2|8});this.world.addBody(this.bar);
    this.startX=x;this.world.time=0;
  }
  createPole(x){
    const count=9,len=.62,dir=V(-.932,.362,0),tip=V(x+5.32,.16,0);
    const q=new C.Quaternion();q.setFromEuler(0,0,Math.atan2(dir.y,dir.x)-Math.PI/2);
    // Carry as one rigid weighted object. On planting it becomes nine physical flex sections.
    this.poleRoot=new C.Body({mass:count*.14,position:tip.vadd(dir.scale(count*len/2)),quaternion:q.clone(),linearDamping:.12,angularDamping:.3,collisionFilterGroup:8,collisionFilterMask:1|4});
    this.poleRoot.addShape(new C.Box(V(.025,count*len/2,.025)));this.world.addBody(this.poleRoot);
    for(let i=0;i<count;i++){
      const b=new C.Body({mass:.14,position:tip.vadd(dir.scale((i+.5)*len)),quaternion:q.clone(),linearDamping:.12,angularDamping:.22,collisionFilterGroup:8,collisionFilterMask:1|4});
      b.addShape(new C.Box(V(.025,len/2,.025)));this.pole.push(b);
    }
    this.attachPoleGrips();
  }
  attachPoleGrips(){
    for(const [name,index,offset] of [['rightHand',7,.10],['leftHand',8,-.10]]){
      const body=this.poleRoot||this.pole[index],pivot=this.poleRoot?V(0,(index+.5)*.62-9*.62/2+offset,0):V(0,offset,0);
      const j=new C.PointToPointConstraint(this.bodies[name],V(0,-.02,0),body,pivot,2e3);this.world.addConstraint(j);this.grips.push(j);
    }
  }
  syncPole(){
    if(!this.poleRoot)return;
    for(let i=0;i<this.pole.length;i++){
      const b=this.pole[i],offset=V(0,(i+.5)*.62-9*.62/2,0);this.poleRoot.pointToWorldFrame(offset,b.position);b.quaternion.copy(this.poleRoot.quaternion);b.angularVelocity.copy(this.poleRoot.angularVelocity);
      b.velocity.copy(this.poleRoot.velocity.vadd(this.poleRoot.angularVelocity.cross(b.position.vsub(this.poleRoot.position))));
    }
  }
  setPoleFlexible(){
    if(!this.poleRoot)return;
    this.syncPole();for(const j of this.grips)this.world.removeConstraint(j);this.grips=[];this.world.removeBody(this.poleRoot);this.poleRoot=null;
    for(const b of this.pole)this.world.addBody(b);
    for(let i=1;i<this.pole.length;i++){
      const j=new C.HingeConstraint(this.pole[i-1],this.pole[i],{pivotA:V(0,.31,0),pivotB:V(0,-.31,0),axisA:V(0,0,1),axisB:V(0,0,1),maxForce:4e3,collideConnected:false});j.enableMotor();j.setMotorMaxForce(20);this.world.addConstraint(j);this.poleJoints.push(j);
    }
    this.attachPoleGrips();
  }
  dropBar(){if(this.bar.type!==C.Body.DYNAMIC){this.bar.type=C.Body.DYNAMIC;this.bar.mass=.8;this.bar.updateMassProperties();this.bar.wakeUp();this.bar.angularVelocity.set(.7,0,1.3);}}
  releasePole(){for(const j of this.grips)this.world.removeConstraint(j);this.grips=[];}
  disableMotors(){for(const j of Object.values(this.joints))j.hinge.disableMotor?.();}
  begin(){this.reset(-14,'run');}
  stepFoot(side){
    if(this.phase!=='run'||!['left','right'].includes(side))return false;
    const gap=this.time-this.lastStepTime;
    if(gap<.12){this.cadence='SLOW THE TAPS';return false;}
    this.footTimes[side]=this.time;
    if(side===this.lastFoot){this.runDrive*=.65;this.cadence='ALTERNATE D → L';this.bodies.hips.torque.z+=side==='left'?12:-12;}
    else{this.runDrive=Math.min(9.0,this.runDrive+(gap<.75?2.3:1.7));this.cadence=gap<.75?'NICE RHYTHM':'KEEP ALTERNATING';}
    // A raised pole amplifies the side-to-side weight transfer of each footfall.
    if(this.poleLift>.1)this.bodies.hips.applyImpulse(V(0,0,(side==='left'?1:-1)*1.8*this.poleLift*this.poleLift),V(0,.5,0));
    this.lastFoot=side;this.lastStepTime=this.time;return true;
  }
  plant(){
    if(this.phase!=='run')return false;
    const hip=this.bodies.hips, speed=hip.velocity.x, x=hip.position.x;
    if(this.poleLift>.55||this.pole[0].pointToWorldFrame(V(0,-.31,0)).y>1.7){this.crash('The pole tip was too high. Release H before the plant box to lower it.');return false;}
    const quality=clamp(1-Math.abs(x+3.65)/1.55,0,1);this.launchQuality=quality;
    if(quality<.15||speed<3.2){this.crash(speed<3.2?'Not enough speed. Alternate D and L to build your run-up.':'Missed the plant box. Plant inside the lime zone.');return false;}
    this.setPoleFlexible();this.phase='vault';this.phaseTime=0;this.vaultTime=0;
    // Anchor the physical tip in the plant box. Joint springs store/release the pole bend.
    this.anchor=new C.Body({mass:0,position:this.pole[0].pointToWorldFrame(V(0,-.31,0)),collisionFilterMask:0});this.anchor.position.y=.05;this.world.addBody(this.anchor);
    this.anchorJoint=new C.PointToPointConstraint(this.anchor,V(),this.pole[0],V(0,-.31,0),8e3);this.world.addConstraint(this.anchorJoint);
    // Training assistance adds an impulse, not a trajectory: all subsequent motion is integrated by gravity and constraints.
    const vy=6.8+quality*1.7+clamp(speed-4,0,4)*.32;
    for(const b of Object.values(this.bodies)){b.velocity.y=vy;b.velocity.x=4.7+quality*.9;}
    return true;
  }
  crash(reason){if(['landed','crash'].includes(this.phase))return;this.reason=reason;this.phase='crash';this.phaseTime=0;this.releasePole();this.disableMotors();this.bodies.chest.angularVelocity.z=-3.5;this.bodies.head.angularVelocity.z=2;}
  land(){
    if(this.phase==='landed')return;
    const clean=!this.barHit&&this.passed&&this.landingSurface==='pad'&&this.launchQuality>.15;
    this.result={clean,height:this.height,peak:this.maxHeight,impact:this.peakImpact,reason:clean?'A clean clearance. The crowd can’t believe it either.':this.barHit?'You clipped the crossbar. Tuck earlier and keep holding Space.':this.reason||'Almost. Build more speed and tuck over the bar.',review:clean?'SURPRISINGLY ALIVE':this.peakImpact>8?'CARTOON CASUALTY':'BRUISED EGO'};
    this.phase='landed';this.phaseTime=0;this.disableMotors();this.releasePole();
    if(!clean&&this.peakImpact>7){this.breakName='leftLowerArm';const j=this.joints[this.breakName];this.world.removeConstraint(j.hinge);const loose=new C.ConeTwistConstraint(this.bodies.leftUpperArm,this.bodies.leftLowerArm,{pivotA:V(0,-.45,.025),pivotB:V(),axisA:V(0,-1,0),axisB:V(0,-1,0),angle:1.9,twistAngle:1.8,collideConnected:false,maxForce:2e4});this.world.addConstraint(loose);this.result.review='LEFT ELBOW: OUT OF OFFICE';}
  }
  aimArms(){
    if(!this.grips.length)return;
    for(const [side,index,offset] of [['left',8,-.10],['right',7,.10]]){
      const upper=this.bodies[side+'UpperArm'],shoulder=upper.position;
      const pitch=Math.atan2(-.15,.4)+this.poleLift*1.05,span=Math.hypot(.4,.15);
      const goal=['preview','ready','run'].includes(this.phase)?this.bodies.chest.pointToWorldFrame(V(.48+(side==='right'?Math.cos(pitch)*span:0),.48+(side==='right'?Math.sin(pitch)*span:0),0)):this.pole[index].pointToWorldFrame(V(0,offset,0));
      if(['preview','ready','run'].includes(this.phase)){
        const hand=this.bodies[side+'Hand'],relativeVelocity=hand.velocity.vsub(this.bodies.chest.velocity),error=goal.vsub(hand.position),stiffness=1200+this.poleLift*1400,damping=38+this.poleLift*30,limit=220+this.poleLift*200;
        hand.force.vadd(V(clamp(error.x*stiffness-relativeVelocity.x*damping,-limit,limit),clamp(error.y*stiffness-relativeVelocity.y*damping,-limit,limit),clamp(error.z*stiffness-relativeVelocity.z*damping,-limit,limit)),hand.force);
        this.joints[side+'LowerArm'].hinge.setMotorMaxForce(8);
      }else this.joints[side+'LowerArm'].hinge.setMotorMaxForce(110);
      const delta=goal.vsub(shoulder),distance=clamp(delta.length(),.12,.86),dir=delta.unit();
      let bend=V(0,-1,0);bend=bend.vsub(dir.scale(bend.dot(dir)));if(bend.length()<.01)bend=V(1,0,0);bend.normalize();
      const a=clamp((.45*.45-.42*.42+distance*distance)/(2*distance),.01,.445),h=Math.sqrt(Math.max(0,.45*.45-a*a));
      const elbow=shoulder.vadd(dir.scale(a)).vadd(bend.scale(h));
      const u=elbow.vsub(shoulder).unit(),l=goal.vsub(elbow).unit();let normal=u.cross(l);if(normal.length()<.01)normal=V(0,0,1);normal.normalize();
      const orient=direction=>{const q=new C.Quaternion().setFromVectors(V(0,-1,0),direction);const twist=new C.Quaternion().setFromVectors(q.vmult(V(0,0,1)),normal);return twist.mult(q);};
      const target=orient(u),lowerTarget=orient(l);this.joints[side+'UpperArm'].targetQ=target;
      const relative=target.conjugate().mult(lowerTarget);this.joints[side+'LowerArm'].target=2*Math.atan2(relative.z,relative.w);
      this.joints[side+'Hand'].target=0;
    }
  }
  update(dt,controls={}){
    this.accumulator+=Math.min(dt,.1);
    while(this.accumulator>=1/120){this.step(1/120,controls);this.accumulator-=1/120;}
  }
  step(dt,controls={}){
    this.time+=dt;this.phaseTime+=dt;
    const hip=this.bodies.hips,chest=this.bodies.chest;
    const supported=['preview','ready','run'].includes(this.phase);
    if(supported){
      this.poleLift=clamp(this.poleLift+dt*(controls.raise?.58:-.32),0,1);
      this.balanceAssist=1-.82*this.poleLift*this.poleLift;
      if(this.poleRoot){
        // Wrist/arm effort rotates the weighted pole; equal reaction torque acts on the torso.
        const pitch=Math.atan2(-.15,.4)+this.poleLift*1.05,current=this.poleRoot.quaternion.vmult(V(0,-1,0)),desired=V(Math.cos(pitch),Math.sin(pitch),0);
        const perpendicularVelocity=this.poleRoot.angularVelocity.vsub(current.scale(this.poleRoot.angularVelocity.dot(current)));
        const gripMid=this.bodies.leftHand.position.vadd(this.bodies.rightHand.position).scale(.5),lever=this.poleRoot.position.vsub(gripMid),loadTorque=lever.cross(V(0,-this.poleRoot.mass*9.81,0));
        const torque=current.cross(desired).scale(85).vsub(perpendicularVelocity.scale(28)).vsub(loadTorque.scale(Math.min(1,this.poleLift*5)));
        this.poleRoot.torque.vadd(torque,this.poleRoot.torque);chest.torque.vsub(torque,chest.torque);
      }
      this.runDrive*=Math.exp(-dt*.5);
      const running=this.phase==='run'&&this.runDrive>.1;
      const targetSpeed=running?this.runDrive:0;
      // Soft balance and propulsion assistance: forces only, never animated body positions.
      const targetY=1.27+(running?.045*Math.sin(this.time*19):0);
      hip.force.y+=(targetY-hip.position.y)*2400-hip.velocity.y*220+440;
      chest.torque.z+=-wrap(angle(chest)-(running?-.10:0))*650*this.balanceAssist-chest.angularVelocity.z*65*Math.sqrt(this.balanceAssist);
      hip.torque.z+=-angle(hip)*280*this.balanceAssist-hip.angularVelocity.z*40*Math.sqrt(this.balanceAssist);
      for(const b of [hip,chest]){const sign=b.quaternion.w<0?-1:1;b.torque.x+=-b.quaternion.x*sign*900*this.balanceAssist-b.angularVelocity.x*65*Math.sqrt(this.balanceAssist);b.torque.y+=-b.quaternion.y*sign*900*this.balanceAssist-b.angularVelocity.y*65*Math.sqrt(this.balanceAssist);}
      hip.force.x+=clamp((targetSpeed-hip.velocity.x)*110,-500,500);
      if(!running)hip.force.x+=(this.startX-hip.position.x)*45;
      else this.startX=hip.position.x;

      for(const [name,j] of Object.entries(this.joints)){
        const side=name.startsWith('left')?1:-1;
        j.target=0;
        const foot=name.startsWith('left')?'left':'right';const age=this.time-this.footTimes[foot];const phase=clamp(age/.52,0,1);
        if(name.endsWith('UpperLeg'))j.target=running&&age<.7?.72-1.12*phase:.03*side;
        if(name.endsWith('LowerLeg'))j.target=running&&age<.7?-Math.sin(phase*Math.PI)*.9:-.03;
        if(name.endsWith('UpperArm'))j.target=name.startsWith('left')?1.72:1.23;
        if(name.endsWith('LowerArm'))j.target=.06;
        if(name==='head')j.target=.05*Math.sin(this.time*1.4);
      }
      if(this.phase==='run'&&this.phaseTime>.8&&chest.quaternion.vmult(V(0,1,0)).y<.60)this.crash('The raised pole pulled you off balance. Use shorter H holds and a steadier D/L rhythm.');
      if(this.phase==='run'&&hip.position.x>-2.0)this.crash('You ran past the plant box. Press Space in the lime zone.');
    }else if(this.phase==='vault'){
      this.vaultTime+=dt;
      chest.torque.z+=(.5-angle(chest))*80-chest.angularVelocity.z*12;
      // Optional easy-mode spring boost during pole loading, scaled by accuracy.
      hip.force.y+=210*this.launchQuality;
      for(const [name,j] of Object.entries(this.joints)){j.target=name.endsWith('UpperArm')?2.8:name.endsWith('UpperLeg')?-.6:name.endsWith('LowerLeg')?-1:0;}
      if(this.vaultTime>.24){this.releasePole();this.phase='flight';this.phaseTime=0;}
    }else if(this.phase==='flight'){
      this.tucked=!!controls.tuck;
      // Active joints pull knees up; modest balance torque helps the beginner orient.
      const desired=this.tucked?-1.15:-.3;
      hip.torque.z+=wrap(desired-angle(hip))*350-hip.angularVelocity.z*65;
      chest.torque.z+=wrap(desired-angle(chest))*180-chest.angularVelocity.z*35;
      for(const b of [hip,chest]){const sign=b.quaternion.w<0?-1:1;b.torque.x+=-b.quaternion.x*sign*200-b.angularVelocity.x*25;b.torque.y+=-b.quaternion.y*sign*200-b.angularVelocity.y*25;}
      for(const [name,j] of Object.entries(this.joints)){j.target=name.endsWith('UpperLeg')?(this.tucked?-1.5:.15):name.endsWith('LowerLeg')?(this.tucked?-1.9:-.1):name.endsWith('UpperArm')?2.7:name.endsWith('LowerArm')?.6:0;}
      if(hip.position.x>=2.3&&!this.crossingChecked){this.crossingChecked=true;this.overBar=hip.position.y>this.height+.12;}
      if(hip.position.x>3.15&&this.overBar)this.passed=true;
      if(this.barHit)this.crash('That crossbar had other plans.');
    }
    if(!['crash','landed'].includes(this.phase))this.aimArms();
    if(!['crash','landed'].includes(this.phase))for(const j of Object.values(this.joints)){
      if(j.ball){
        if(!this.grips.length)j.targetQ.setFromEuler(0,0,j.target);
        let errorQ=j.targetQ.mult(j.body.quaternion.conjugate());const sign=errorQ.w<0?-1:1;
        const torque=V(clamp(errorQ.x*sign*350-j.body.angularVelocity.x*3,-45,45),clamp(errorQ.y*sign*350-j.body.angularVelocity.y*3,-45,45),clamp(errorQ.z*sign*350-j.body.angularVelocity.z*3,-45,45));
        j.body.torque.vadd(torque,j.body.torque);this.bodies[j.parent].torque.vsub(torque,this.bodies[j.parent].torque);continue;
      }
      const relative=this.bodies[j.parent].quaternion.conjugate().mult(j.body.quaternion);const error=wrap(j.target-2*Math.atan2(relative.z,relative.w));
      j.hinge.setMotorSpeed(clamp(-error*12,-13,13));
    }
    // Light out-of-plane stabilizer in easy mode; crashes are free in all three axes.
    for(const b of Object.values(this.bodies))if(!['crash','landed'].includes(this.phase)&&!/(Arm|Hand)$/.test(b.name)){
      b.force.z+=-(b.position.z-b.restZ)*120-b.velocity.z*18;
    }
    // Elastic pole: torque springs align adjacent physical sections, permitting visible bending.
    for(let i=1;!this.poleRoot&&i<this.pole.length;i++){
      const a=this.pole[i-1],b=this.pole[i],relative=a.quaternion.conjugate().mult(b.quaternion),e=wrap(2*Math.atan2(relative.z,relative.w));
      if(!this.poleJoints[i-1].setMotorSpeed)continue;this.poleJoints[i-1].setMotorMaxForce(20);this.poleJoints[i-1].setMotorSpeed(clamp(e*(supported?65:18),-20,20));
    }
    this.world.step(dt);this.syncPole();
    this.maxHeight=Math.max(this.maxHeight,hip.position.y);
    if(['flight','vault','crash'].includes(this.phase)&&this.phaseTime>5){this.landingSurface='track';this.land();}
    if(this.phase==='run'&&this.phaseTime>30)this.crash('The officials got hungry. A little more running next time.');
    if(!Number.isFinite(hip.position.x)||hip.position.y<-5){this.reason='A spectacular physics mishap. Try another run.';this.landingSurface='track';this.land();}
  }
  snapshot(){return {phase:this.phase,x:this.bodies.hips.position.x,y:this.bodies.hips.position.y,speed:this.bodies.hips.velocity.x,cadence:this.cadence,poleLift:this.poleLift,poleTipHeight:this.pole[0].pointToWorldFrame(V(0,-.31,0)).y,balanceAssist:this.balanceAssist,lastFoot:this.lastFoot,barHit:this.barHit,height:this.height,peak:this.maxHeight,result:this.result,bodyCount:Object.keys(this.bodies).length,jointCount:Object.keys(this.joints).length};}
}

import * as THREE from 'three';
import * as C from 'cannon-es';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {VaultPhases} from './vault-phases.js';
import {PoleMomentum} from './pole-momentum.js';
import {RUN_START,WALL_X,WALL_HEIGHT,MAP_EDGE,launchPower} from './vault-power.js';

const SCALE=5.58/1.95, V=(x=0,y=0,z=0)=>new C.Vec3(x,y,z), clamp=THREE.MathUtils.clamp;
const PHYSICAL=['hips','chest','head',...['Right','Left'].flatMap(s=>['upper_arm','forearm','hand','thigh','shin','foot'].map(p=>s+'_'+p))];
const PARENT={hips:null,chest:'hips',head:'chest'};
for(const s of ['Right','Left'])Object.assign(PARENT,{[s+'_upper_arm']:'chest',[s+'_forearm']:s+'_upper_arm',[s+'_hand']:s+'_forearm',[s+'_thigh']:'hips',[s+'_shin']:s+'_thigh',[s+'_foot']:s+'_shin'});
const toThree=v=>new THREE.Vector3(v.x,v.y,v.z);
const cannonQuaternion=q=>new C.Quaternion(q.x,q.y,q.z,q.w);
const transform=(body,scale=new THREE.Vector3(1,1,1))=>new THREE.Matrix4().compose(toThree(body.position),new THREE.Quaternion(body.quaternion.x,body.quaternion.y,body.quaternion.z,body.quaternion.w),scale);

/** Reviewed pose phases are player-controlled; release/failure hands the skin to Cannon bodies. */
export class RiggedVaultGame {
  constructor(){
    this.world=new C.World({gravity:V(0,-9.81,0)});this.world.solver.iterations=32;this.world.defaultContactMaterial.friction=.55;this.world.defaultContactMaterial.restitution=.04;
    this.ground=new C.Body({mass:0,shape:new C.Plane(),collisionFilterGroup:1});this.ground.quaternion.setFromEuler(-Math.PI/2,0,0);this.world.addBody(this.ground);
    this.pad=new C.Body({mass:0,shape:new C.Box(V(3.6,.39,2.5)),position:V(6.5,.39,0),collisionFilterGroup:1});this.world.addBody(this.pad);
    this.wall=new C.Body({mass:0,shape:new C.Box(V(.4,WALL_HEIGHT/2,4.5)),position:V(WALL_X,WALL_HEIGHT/2,0),collisionFilterGroup:1});this.world.addBody(this.wall);
    this.height=4.2;this.weightKg=95;this.motion=new VaultPhases();this.momentum=new PoleMomentum();this.model=null;this.reset(-3.9,'preview');
  }
  async load(scene){
    const gltf=await new GLTFLoader().loadAsync('/assets/pepe-plant-animated.glb');
    this.model=gltf.scene;this.model.name='Pepe_ManualVault';this.model.scale.setScalar(SCALE);this.model.rotation.y=Math.PI/2;scene.add(this.model);
    this.model.getObjectByName('PlantBox_Anchor').visible=false;
    this.model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false}});
    this.character=this.model.getObjectByName('Pepe_Plant_Rig');this.poleVisual=this.model.getObjectByName('VaultPole');
    this.mixer=new THREE.AnimationMixer(this.model);this.action=this.mixer.clipAction(gltf.animations[0]);this.action.setLoop(THREE.LoopOnce,1);this.action.clampWhenFinished=true;this.action.play();
    this.bones=[];this.character.traverse(b=>{if(b.isBone)this.bones.push(b)});
    this.sample(1);this.restPose=this.bones.map(b=>({bone:b,position:b.position.clone(),quaternion:b.quaternion.clone(),scale:b.scale.clone()}));
    this.gait=[];
    for(let frame=1;frame<=49;frame++){
      this.sample(frame);const row={};for(const bone of this.bones)if(/_(thigh|shin|foot)/.test(bone.name))row[bone.name]={position:bone.position.clone(),quaternion:bone.quaternion.clone(),scale:bone.scale.clone()};this.gait.push(row);
    }
    this.sample(73);this.model.position.set(0,0,0);this.model.updateMatrixWorld(true);const tip=this.model.getObjectByName('PoleFlex_20').getWorldPosition(new THREE.Vector3());
    this.boxAnchorRoot=new THREE.Vector3(.9,.04,0).sub(tip);this.anchorRoot=this.boxAnchorRoot.clone();
    this.reset(this.runX,this.phase);return this;
  }
  sample(frame){this.action.time=(frame-1)/30;this.mixer.update(0);}
  reset(x=RUN_START,mode='ready'){
    for(const c of [...this.world.constraints])this.world.removeConstraint(c);
    for(const b of [...this.world.bodies])if(b!==this.ground&&b!==this.pad&&b!==this.wall)this.world.removeBody(b);
    this.motion.reset();this.momentum.reset();this.poseVelocity={};this.lastPosePosition={};this.launchVelocity=null;this.time=0;this.phaseTime=0;this.accumulator=0;this.runX=x;this.startX=x;this.speed=0;this.runDrive=0;this.lastStepTime=-10;this.lastFoot=null;this.footTimes={left:-10,right:-10};this.phase=mode;this.cadence='TAP D, THEN L';this.poleLift=0;this.balanceAssist=1;this.maxHeight=0;this.barHit=false;this.peakImpact=0;this.launchQuality=0;this.approachSpeed=0;this.launchBoost=0;this.anchorX=null;this.plantX=null;if(this.boxAnchorRoot)this.anchorRoot=this.boxAnchorRoot.clone();this.wallHit=false;this.outOfBounds=false;this.stepCount=0;this.farthestX=x;this.passed=false;this.crossingChecked=false;this.overBar=false;this.result=null;this.reason=null;this.breakName=null;this.ragdoll=false;this.joints={};this.pole=[];this.grips=[];this.bodies={hips:new C.Body({position:V(x,1.24,0)}),chest:new C.Body({position:V(x,1.7,0)})};
    this.bar=new C.Body({mass:.8,shape:new C.Box(V(.045,.045,2.05)),position:V(2.3,this.height,0),collisionFilterGroup:4,collisionFilterMask:1|2});this.world.addBody(this.bar);
    this.barSupport=new C.Body({mass:0,position:this.bar.position.clone(),collisionFilterMask:0});this.world.addBody(this.barSupport);this.barLock=new C.LockConstraint(this.barSupport,this.bar,{maxForce:1e5});this.world.addConstraint(this.barLock);
    if(this.model){this.action.stop();this.action.reset().play();for(const p of this.restPose){p.bone.position.copy(p.position);p.bone.quaternion.copy(p.quaternion);p.bone.scale.copy(p.scale);}this.applyPose();this.createBodies();this.syncBodies();}
  }
  setBarHeight(height){this.height=height;if(['preview','ready'].includes(this.phase)){this.bar.position.y=height;this.barSupport.position.y=height;this.bar.velocity.setZero();}}
  setWeight(weightKg){
    if(!['preview','ready','landed'].includes(this.phase))return false;
    this.weightKg=clamp(Number(weightKg)||95,50,180);
    if(this.physical)for(const b of Object.values(this.physical)){b.originalMass=b.baseMass*this.weightKg/46.6;b.mass=b.originalMass;b.updateMassProperties();}
    return true;
  }
  createBodies(){
    this.physical={};this.bodies={};this.model.updateMatrixWorld(true);
    for(const name of PHYSICAL){
      const bone=this.model.getObjectByName(name),q=bone.getWorldQuaternion(new THREE.Quaternion()),p=bone.getWorldPosition(new THREE.Vector3());
      let length=.12,radius=.05,mass=2,center=.05,size;
      if(name==='hips'){size=[.115,.075,.10];center=.035;mass=8;}
      else if(name==='chest'){size=[.17,.115,.09];center=.095;mass=12;}
      else if(name==='head'){size=[.13,.12,.12];center=.13;mass=4;}
      else if(name.endsWith('upper_arm')){length=.14;radius=.045;mass=2.2;}
      else if(name.endsWith('forearm')){length=.115;radius=.033;mass=1.4;}
      else if(name.endsWith('hand')){length=.04;radius=.028;mass=.5;}
      else if(name.endsWith('thigh')){length=.185;radius=.054;mass=4;}
      else if(name.endsWith('shin')){length=.19;radius=.036;mass=2.6;}
      else if(name.endsWith('foot')){length=.065;radius=.031;mass=.6;}
      if(!size){size=[radius,length*.45,radius];center=length*.45;}
      const body=new C.Body({mass:mass*this.weightKg/46.6,type:C.Body.KINEMATIC,position:V(p.x,p.y,p.z),quaternion:cannonQuaternion(q),linearDamping:.10,angularDamping:.25,collisionFilterGroup:2,collisionFilterMask:1|4});body.addShape(new C.Box(V(...size.map(v=>v*SCALE))),V(0,center*SCALE,0));body.name=name;body.baseMass=mass;body.originalMass=mass*this.weightKg/46.6;this.world.addBody(body);this.physical[name]=body;
      body.addEventListener('collide',e=>{if(e.body===this.bar){this.barHit=true;this.dropBar();}if(e.body===this.wall&&this.ragdoll&&!this.result){this.wallHit=true;this.reason='Cleared the bar. Found the stadium wall. The wall won.';this.phase='crash';this.peakImpact=Math.max(this.peakImpact,Math.abs(e.contact.getImpactVelocityAlongNormal()));}
      if((e.body===this.ground||e.body===this.pad)&&this.ragdoll){this.peakImpact=Math.max(this.peakImpact,Math.abs(e.contact.getImpactVelocityAlongNormal()));if(this.phaseTime>.22&&['hips','chest','head'].includes(name)){this.landingSurface=e.body===this.pad?'pad':'track';this.land();}}});
      this.bodies[name]=body;
    }
    for(const s of ['Right','Left'])for(const [part,legacy] of [['upper_arm','UpperArm'],['forearm','LowerArm'],['hand','Hand'],['thigh','UpperLeg'],['shin','LowerLeg']])this.bodies[s.toLowerCase()+legacy]=this.physical[s+'_'+part];
  }
  applyPose(){
    if(!this.model)return;this.sample(this.motion.frame);
    if(['preview','ready','run'].includes(this.phase)){
      for(const side of ['Left','Right']){
        const age=this.time-this.footTimes[side.toLowerCase()],u=clamp(age/.56,0,1),wave=Math.sin(u*Math.PI),frame=side==='Left'?1+48*u:25-24*wave;
        const index=age>=0&&age<.56?clamp(Math.round(frame)-1,0,48):(side==='Left'?0:24),pose=this.gait[index];
        for(const bone of this.bones){const value=pose[bone.name];if(value&&bone.name.startsWith(side+'_')){bone.position.copy(value.position);bone.quaternion.copy(value.quaternion);bone.scale.copy(value.scale);}}
      }
      this.model.position.set(this.runX-.10,.02,0);this.model.rotation.set(0,Math.PI/2,0);
    }else if(this.phase==='vault'){
      const t=clamp((this.motion.frame-this.plantFrame)/(73-this.plantFrame),0,1);this.model.position.lerpVectors(this.plantRoot,this.anchorRoot,t);
      const turn=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),-this.momentum.angle);
      this.model.quaternion.setFromEuler(new THREE.Euler(0,Math.PI/2,0));this.model.quaternion.premultiply(turn);
      const anchor=new THREE.Vector3(this.anchorX,.04,0);this.model.position.sub(anchor).applyQuaternion(turn).add(anchor);
    }
    this.model.updateMatrixWorld(true);
  }
  syncBodies(dt=0){
    if(!this.physical)return;
    for(const [name,b]of Object.entries(this.physical)){
      const bone=this.model.getObjectByName(name),p=bone.getWorldPosition(new THREE.Vector3()),q=bone.getWorldQuaternion(new THREE.Quaternion());
      if(dt&&this.lastPosePosition[name]){
        const measured=p.clone().sub(this.lastPosePosition[name]).divideScalar(dt);
        this.poseVelocity[name]??=new THREE.Vector3();this.poseVelocity[name].lerp(measured,1-Math.exp(-dt*22));
      }
      this.lastPosePosition[name]=p.clone();
      b.position.set(p.x,p.y,p.z);b.quaternion.set(q.x,q.y,q.z,q.w);b.velocity.setZero();b.angularVelocity.setZero();b.aabbNeedsUpdate=true;
    }
  }
  stepFoot(side){
    if(this.phase!=='run'||!['left','right'].includes(side))return false;const gap=this.time-this.lastStepTime;if(gap<.12){this.cadence='SLOW THE TAPS';return false;}
    this.footTimes[side]=this.time;this.stepCount++;if(side===this.lastFoot){this.runDrive*=.65;this.cadence='ALTERNATE D → L';}else{this.runDrive=Math.min(15/Math.sqrt(this.weightKg/95),this.runDrive+(gap<.38?1.55:gap<.75?1.0:.65)/(this.weightKg/95));this.cadence=this.speed>10?'TOO MUCH LEG DAY':gap<.75?'NICE RHYTHM':'KEEP ALTERNATING';}
    this.lastStepTime=this.time;this.lastFoot=side;return true;
  }
  plant(){
    if(this.phase!=='run')return false;this.approachSpeed=this.speed;this.launchQuality=.35+.65*clamp((this.motion.frame-1)/48,0,1);
    if(this.speed<3.2){this.crash('The pole dug in before you had enough speed. Alternate D and L first.');return false;}
    this.plantX=this.runX;this.anchorX=this.runX+4.55;this.anchorRoot=this.boxAnchorRoot.clone();this.anchorRoot.x+=this.anchorX-.9;
    this.phase='vault';this.phaseTime=0;this.plantFrame=this.motion.frame;this.plantRoot=this.model.position.clone();const rate=145+this.speed*3;this.momentum.plant(this.approachSpeed,this.launchQuality,(121-this.plantFrame)/rate,this.weightKg);this.motion.plant(rate);this.grips=['right','left'];return true;
  }
  swing(){return this.phase==='vault'&&this.momentum.swing(this.motion.frame);}
  throw(){
    if(this.phase!=='vault'||!this.momentum.throw(this.motion.frame))return false;
    return this.motion.throw();
  }
  release(){
    if(this.phase!=='vault'||!this.momentum.throwUsed)return false;
    const incoming=this.poseVelocity.hips??new THREE.Vector3(this.approachSpeed,0,0);
    const power=launchPower({speed:this.approachSpeed,quality:this.launchQuality,charge:this.momentum.charge,swingTiming:this.momentum.swingTiming,throwTiming:this.momentum.throwTiming,velocity:incoming,weightKg:this.weightKg});
    this.launchBoost=power.boost;this.launchVelocity={x:power.x,y:power.y};
    this.motion.release();this.momentum.active=false;this.phase='flight';this.phaseTime=0;
    this.makeDynamic(V(power.x,power.y,0),power.spin);return true;
  }
  crash(reason){
    if(['crash','landed'].includes(this.phase))return;
    const velocity=this.phase==='vault'?(this.poseVelocity.hips??new THREE.Vector3(this.speed,0,0)):new THREE.Vector3(this.speed,0,0);
    this.reason=reason;this.phase='crash';this.phaseTime=0;this.momentum.active=false;
    this.makeDynamic(V(clamp(velocity.x,-12,18),clamp(velocity.y,-12,14),0),-2.4);
  }
  makeDynamic(velocity,spin){
    if(this.ragdoll||!this.physical)return;this.model.updateMatrixWorld(true);this.syncBodies();this.ragdoll=true;this.grips=[];this.follow=[];const hip=this.physical.hips,omega=V(0,0,spin);
    for(const [name,b]of Object.entries(this.physical)){b.type=C.Body.DYNAMIC;b.mass=b.originalMass;b.updateMassProperties();const relative=(this.poseVelocity[name]??new THREE.Vector3()).clone().sub(this.poseVelocity.hips??new THREE.Vector3()).clampLength(0,5).multiplyScalar(.3);b.velocity.copy(velocity.vadd(omega.cross(b.position.vsub(hip.position))).vadd(V(relative.x,relative.y,relative.z)));b.angularVelocity.copy(omega);b.wakeUp();const parent=PARENT[name];if(parent){const a=this.physical[parent],point=b.position.clone(),j=new C.ConeTwistConstraint(a,b,{pivotA:a.pointToLocalFrame(point),pivotB:V(),axisA:a.vectorToLocalFrame(b.quaternion.vmult(V(0,1,0))),axisB:V(0,1,0),angle:name==='chest'?.4:name==='head'?.6:1.35,twistAngle:name.includes('hand')?.4:.8,maxForce:3e4,collideConnected:false});this.world.addConstraint(j);this.joints[name]=j;}}
    for(const bone of this.bones){let driver=bone.name;if(!this.physical[driver]){if(driver.endsWith('clavicle'))driver='chest';else if(driver.endsWith('shoulder_cap'))driver=driver.replace('shoulder_cap','upper_arm');else driver=driver.replace('_swing','').replace('_twist','');}if(!this.physical[driver])driver='chest';this.follow.push({bone,body:this.physical[driver],offset:transform(this.physical[driver]).invert().multiply(bone.matrixWorld)});}
    // The released pole remains in the planted box, separate from the airborne skin.
    this.model.updateMatrixWorld(true);
  }
  syncRagdoll(){
    for(const {bone,body,offset}of this.follow){const target=transform(body).multiply(offset),local=bone.parent.matrixWorld.clone().invert().multiply(target);local.decompose(bone.position,bone.quaternion,bone.scale);bone.updateMatrix();bone.updateMatrixWorld(true);}
  }
  dropBar(){if(this.barLock){this.world.removeConstraint(this.barLock);this.barLock=null;this.bar.angularVelocity.set(.6,0,1.2);this.bar.wakeUp();}}
  land(){
    if(this.result)return;const clean=!this.wallHit&&!this.outOfBounds&&!this.barHit&&this.passed&&this.landingSurface==='pad'&&this.launchQuality>.15;
    this.result={clean,height:this.height,peak:this.maxHeight,impact:this.peakImpact,distance:Math.max(0,this.farthestX-(this.anchorX??.9)),boost:this.launchBoost,wallHit:this.wallHit,outOfBounds:this.outOfBounds,reason:this.outOfBounds?'Pepe has left the stadium. The judges are checking nearby airports.':this.wallHit?this.reason:clean?'A clean clearance. The crowd can’t believe it either.':this.barHit?'Clipped the crossbar. Charge Space, time J with the surge, then K to throw.':this.reason||(this.farthestX<2.3?'Planted too early for that speed. Build more pace, or plant closer to the bar.':null)||(this.farthestX>11?'Overshot the mat. A little less leg day next time.':null)||'Almost. Carry your speed into the plant, time J, then throw with K.',review:this.outOfBounds?'FLIGHT CANCELLED':this.wallHit?'WALL: 1 · PEPE: 0':clean?'SURPRISINGLY ALIVE':this.peakImpact>8?'CARTOON CASUALTY':'BRUISED EGO'};this.phase='landed';this.phaseTime=0;if(!clean&&this.peakImpact>7)this.breakName='leftLowerArm';
  }
  update(dt,controls={}){this.accumulator+=Math.min(dt,.1);while(this.accumulator>=1/120){this.step(1/120,controls);this.accumulator-=1/120;}}
  step(dt,controls){
    if(!this.model)return;this.time+=dt;this.phaseTime+=dt;
    if(!this.ragdoll){
      if(this.phase==='vault')this.momentum.update(dt,{charge:controls.charge});
      this.motion.update(dt,{raise:controls.raise,swing:controls.swing&&this.momentum.swingUsed});this.poleLift=clamp((this.motion.frame-1)/48,0,1);this.balanceAssist=1-.45*this.poleLift;
      if(this.phase==='run'){this.runDrive*=Math.exp(-dt*.5);this.speed=THREE.MathUtils.damp(this.speed,this.runDrive*(1-.13*this.poleLift),4/Math.sqrt(this.weightKg/95),dt);this.runX+=this.speed*dt;}
      this.applyPose();this.syncBodies(dt);
      if(this.phase==='vault'){this.speed=Math.max(0,this.poseVelocity.hips?.x??0);if(this.motion.state==='inverted')this.release();else if(this.momentum.failed)this.crash('The surge faded. Time J with the green cue, then tap K to throw.');}
      if(this.phase==='run'&&this.runX>1.4)this.crash('Ran into the standards. Lower with H and plant with Space anywhere before the bar.');
    }
    this.world.step(dt);if(this.ragdoll)this.syncRagdoll();const hip=this.bodies.hips;this.farthestX=Math.max(this.farthestX,hip.position.x);this.maxHeight=Math.max(this.maxHeight,hip.position.y);
    if(this.phase==='flight'){
      if(hip.position.x>=2.3&&!this.crossingChecked){this.crossingChecked=true;this.overBar=hip.position.y>this.height+.12;}
      if(hip.position.x>3.15&&this.overBar)this.passed=true;
    }
    if(this.ragdoll&&!this.result&&(hip.position.x>MAP_EDGE||Math.abs(hip.position.z)>35)){this.outOfBounds=true;this.landingSurface='outside';this.land();}
    if(['flight','crash'].includes(this.phase)&&(this.phaseTime>9||hip.position.y<-4)){this.landingSurface='track';this.land();}
    if(this.phase==='run'&&this.phaseTime>30)this.crash('The officials got hungry. A little more running next time.');
  }
  snapshot(){const tip=this.model?.getObjectByName('PoleFlex_20').getWorldPosition(new THREE.Vector3());return {weightKg:this.weightKg,physicalMass:this.physical?Object.values(this.physical).reduce((sum,b)=>sum+b.originalMass,0):0,momentum:this.momentum.snapshot(),launchVelocity:this.launchVelocity,anchorError:this.anchorX!==null&&this.motion.frame>=73&&tip?tip.distanceTo(new THREE.Vector3(this.anchorX,.04,0)):null,time:this.time,phase:this.phase,technique:this.motion.state,frame:this.motion.frame,x:this.bodies.hips.position.x,y:this.bodies.hips.position.y,speed:this.ragdoll?this.bodies.hips.velocity.x:this.speed,cadence:this.cadence,poleLift:this.poleLift,balanceAssist:this.balanceAssist,lastFoot:this.lastFoot,barHit:this.barHit,height:this.height,peak:this.maxHeight,approachSpeed:this.approachSpeed,launchBoost:this.launchBoost,steps:this.stepCount,startX:this.startX,plantX:this.plantX,anchorX:this.anchorX,wallHit:this.wallHit,outOfBounds:this.outOfBounds,distance:Math.max(0,this.farthestX-(this.anchorX??.9)),result:this.result,bodyCount:this.physical?Object.keys(this.physical).length:0,jointCount:Object.keys(this.joints).length,rigged:!!this.model,ragdoll:this.ragdoll,grips:this.grips.length,feetAboveHead:this.model?Object.fromEntries(['Right','Left'].map(s=>[s,this.model.getObjectByName(s+'_foot').getWorldPosition(new THREE.Vector3()).y-this.model.getObjectByName('head').getWorldPosition(new THREE.Vector3()).y])):null};}
}

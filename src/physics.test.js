import {test} from 'node:test';
import assert from 'node:assert/strict';
import {VaultPhysics} from './physics.js';

function attempt({fps=60,height=4.2,plant=-3.7,tuck=true}={}){
  const p=new VaultPhysics();p.height=height;p.reset(-14,'ready');
  for(let i=0;i<fps*3;i++)p.update(1/fps);
  p.phase='run';let planted=false,nextStep=p.time,foot='left';
  for(let i=0;i<fps*15&&!p.result;i++){
    if(p.time>=nextStep){p.stepFoot(foot);foot=foot==='left'?'right':'left';nextStep=p.time+.28;}
    if(!planted&&p.bodies.hips.position.x>=plant){p.plant();planted=true;}
    p.update(1/fps,{run:true,tuck});
  }
  return p;
}
test('a timed, tucked starter vault clears at 30, 60 and 120 fps',()=>{
  for(const fps of [30,60,120]){const p=attempt({fps});assert.equal(p.result?.clean,true,`${fps} fps: ${p.result?.reason}`);assert.equal(p.barHit,false);assert.equal(p.landingSurface,'pad');assert.equal(p.world.gravity.y,-9.81);}
});
test('a premature plant releases the grips and disables joint motors',()=>{
  const p=new VaultPhysics();p.begin();assert.equal(p.plant(),false);assert.equal(p.phase,'crash');assert.equal(p.grips.length,0);assert.ok(Object.values(p.joints).every(j=>!j.hinge.motorEquation?.enabled));
  for(let i=0;i<400&&!p.result;i++)p.update(1/60);
  assert.equal(p.result.clean,false);
});
test('contact drops the 6 m bar and cannot be scored as success',()=>{
  const p=attempt({height:6});assert.equal(p.barHit,true);assert.equal(p.result.clean,false);assert.equal(p.bar.type,1);assert.ok(p.bar.position.y<6);
});
test('passing under an unreachable bar never counts as a clearance',()=>{
  const p=attempt({height:12});assert.equal(p.barHit,false);assert.equal(p.result.clean,false);assert.equal(p.passed,false);
});
test('reset restores bodies, joints, standing crossbar and clears injury state',()=>{
  const p=attempt({height:6});const count=p.world.bodies.length;p.reset(-14,'ready');assert.equal(Object.keys(p.bodies).length,13);assert.equal(Object.keys(p.joints).length,12);assert.equal(p.barHit,false);assert.equal(p.breakName,null);assert.equal(p.result,null);assert.equal(p.bar.position.y,6);assert.equal(p.grips.length,2);assert.ok(p.world.bodies.length<=count);
});
test('running past the plant zone fails without requiring a plant key',()=>{
  const p=new VaultPhysics();p.begin();for(let i=0;i<1000&&!p.result;i++){if(i%18===0)p.stepFoot(i%36===0?'left':'right');p.update(1/60);}assert.equal(p.result.clean,false);assert.match(p.result.reason,/ran past/);
});

test('holding a foot does not auto-run; alternating feet builds drive and repeated feet cost speed',()=>{
 const p=new VaultPhysics();p.begin();for(let i=0;i<120;i++)p.update(1/60,{run:true});assert.ok(Math.abs(p.bodies.hips.position.x+14)<.8);p.stepFoot('left');const first=p.runDrive;for(let i=0;i<18;i++)p.update(1/60);p.stepFoot('right');assert.ok(p.runDrive>first);const good=p.runDrive;for(let i=0;i<18;i++)p.update(1/60);p.stepFoot('right');assert.ok(p.runDrive<good);assert.equal(p.cadence,'ALTERNATE D → L');
});

test('staggered two-hand grip stays attached with the pole pointing forward',()=>{
  const p=new VaultPhysics();for(let i=0;i<600;i++)p.update(1/60);
  assert.equal(p.phase,'preview');
  for(const grip of p.grips){const a=grip.bodyA.pointToWorldFrame(grip.pivotA),b=grip.bodyB.pointToWorldFrame(grip.pivotB);assert.ok(a.distanceTo(b)<.02,'hand stays on pole');}
  const left=p.bodies.leftHand.position,right=p.bodies.rightHand.position;
  assert.ok(right.x>left.x+.2,'front hand reaches farther along the runway');
  assert.ok(left.y>right.y+.05,'rear hand is higher');
  assert.ok(p.pole[0].position.x>p.bodies.hips.position.x+3,'pole points at the vault');
  assert.ok(Math.abs(p.bodies.leftUpperLeg.position.z-p.bodies.rightUpperLeg.position.z)>.4,'feet sit on opposite sides of the forward-facing body');
});

test('holding H raises the weighted pole progressively; releasing lowers it',()=>{
  const p=new VaultPhysics();for(let i=0;i<180;i++)p.update(1/60);
  const low=p.snapshot().poleTipHeight;
  for(let i=0;i<45;i++)p.update(1/60,{raise:true});const mid=p.snapshot().poleTipHeight;
  for(let i=0;i<45;i++)p.update(1/60,{raise:true});const high=p.snapshot().poleTipHeight;
  assert.ok(mid>low+.8,'tip leaves the ground');assert.ok(high>mid+1,'longer hold lifts higher');assert.ok(p.balanceAssist<.5);assert.ok(p.poleRoot.mass>1,'pole retains physical weight');
  for(let i=0;i<300;i++)p.update(1/60);assert.equal(p.poleLift,0);assert.ok(p.snapshot().poleTipHeight<.2,'release lowers the tip');
});
test('carrying high produces more torso sway under the same D/L inputs',()=>{
  const sway=raise=>{const p=new VaultPhysics();p.begin();let peak=0;for(let i=0;i<180&&!p.result;i++){if(i%18===0)p.stepFoot(i%36===0?'left':'right');p.update(1/60,{raise});peak=Math.max(peak,1-p.bodies.chest.quaternion.vmult({x:0,y:1,z:0}).y);}return peak;};
  assert.ok(sway(true)>sway(false)*1.5);
});
test('an excessively raised pole cannot be planted',()=>{
  const p=new VaultPhysics();p.begin();for(let i=0;i<90;i++)p.update(1/60,{raise:true});assert.equal(p.plant(),false);assert.equal(p.phase,'crash');assert.match(p.reason,/tip was too high/);
});

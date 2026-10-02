import test from 'node:test';
import assert from 'node:assert/strict';
import {PoleMomentum} from './pole-momentum.js';
const advance=(p,seconds,charge=false)=>{for(let i=0;i<Math.round(seconds*120);i++)p.update(1/120,{charge});};
const planted=(weight=95)=>{const p=new PoleMomentum();p.plant(9,1,.4,weight);return p;};
test('plant continues moving without input; timed J adds one impulse and K uses timing',()=>{
 const p=planted();advance(p,.63);assert.ok(p.angle>.3);const before=p.angularVelocity;
 assert.equal(p.throw(169),false);assert.equal(p.swing(121),true);assert.ok(p.swingTiming>.98);assert.ok(p.angularVelocity>before+.35);
 const boosted=p.angularVelocity;assert.equal(p.swing(121),false);assert.equal(p.angularVelocity,boosted);
 assert.equal(p.throw(150),false);assert.equal(p.throwUsed,false);advance(p,.62);assert.equal(p.throw(169),true);assert.ok(p.throwTiming>.98);assert.equal(p.throw(169),false);
 const early=planted();early.swing(73);assert.equal(early.swingTiming,0);
});
test('Space charges only while held, caps at two seconds, and stale swings fail',()=>{
 const p=planted();advance(p,.6,true);assert.ok(Math.abs(p.charge-.3)<1e-9);advance(p,.3);assert.ok(Math.abs(p.charge-.3)<1e-9);
 advance(p,2,true);assert.equal(p.charge,1);advance(p,1);assert.equal(p.failed,true);p.reset();assert.equal(p.charge,0);assert.equal(p.active,false);
});
test('body mass changes spring acceleration and swing response',()=>{
 const light=planted(50),heavy=planted(180);advance(light,.63);advance(heavy,.63);const beforeLight=light.angularVelocity,beforeHeavy=heavy.angularVelocity;
 assert.ok(light.angle>heavy.angle);light.swing(121);heavy.swing(121);assert.ok(light.angularVelocity-beforeLight>(heavy.angularVelocity-beforeHeavy)*3);
});

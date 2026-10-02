import {test} from 'node:test';
import assert from 'node:assert/strict';
import {VaultPhases} from './vault-phases.js';
const advance=(p,seconds,controls={},fps=60)=>{for(let i=0;i<seconds*fps;i++)p.update(1/fps,controls)};
test('J controls the swing and a K tap commits extension and release readiness',()=>{
 const p=new VaultPhases();advance(p,2,{raise:true});assert.equal(p.frame,49);p.plant();advance(p,2);assert.equal(p.frame,121);assert.equal(p.throw(),false);
 advance(p,.25,{swing:true});const middle=p.frame;assert.ok(middle>121&&middle<169);advance(p,1);assert.equal(p.frame,middle);
 advance(p,1,{swing:true});assert.equal(p.frame,169);assert.equal(p.throw(),true);advance(p,.3);assert.equal(p.frame,193);assert.equal(p.state,'inverted');assert.equal(p.release(),true);advance(p,1,{swing:true});assert.equal(p.frame,193);
});
test('phase timings are stable across frame rates and reset clears progression',()=>{
 for(const fps of [30,60,120]){const p=new VaultPhases();p.plant();advance(p,2,{},fps);advance(p,1,{swing:true},fps);p.throw();advance(p,1,{},fps);assert.equal(p.frame,193);p.reset();assert.equal(p.frame,1);assert.equal(p.release(),false);}
});
test('H tap moves pole immediately; short hold lowers fully and release preserves the pose',()=>{
 const p=new VaultPhases();p.lowerPoleTap();assert.equal(p.frame,13);advance(p,.1);assert.equal(p.frame,13);advance(p,.1,{raise:true});assert.ok(p.frame>24);advance(p,.25,{raise:true});assert.equal(p.frame,49);advance(p,1);assert.equal(p.frame,49);p.plant();const frame=p.frame;p.lowerPoleTap();assert.equal(p.frame,frame);
});

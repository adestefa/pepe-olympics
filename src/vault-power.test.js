import test from 'node:test';
import assert from 'node:assert/strict';
import {launchPower,RUN_START,MAP_EDGE} from './vault-power.js';
const launch=(overrides={})=>launchPower({speed:11,quality:1,charge:.3,swingTiming:1,throwTiming:1,velocity:{x:5,y:3},weightKg:95,...overrides});
test('incoming momentum, J/K timing and Space charge all change the launch',()=>{
 assert.ok(-3.65-RUN_START>28);
 assert.ok(launch().x>launch({velocity:{x:0,y:0}}).x);
 assert.ok(launch().x>launch({swingTiming:0}).x+10);
 assert.ok(launch().x>launch({throwTiming:0}).x+10);
 assert.ok(launch({charge:1}).y>launch({charge:0}).y+11);
 const fast=launch({speed:13,charge:1});
 const airtime=(fast.y+Math.sqrt(fast.y*fast.y+2*9.81*4.8))/9.81;
 assert.ok(-1+fast.x*airtime>MAP_EDGE,'strong launch can leave the stadium');
});
test('same technique gives lighter bodies a larger boost without changing gravity',()=>{
 const light=launch({weightKg:50}),heavy=launch({weightKg:180});
 assert.ok(light.x>heavy.x*1.5);assert.ok(light.y>heavy.y*1.5);
 for(const speed of [0,7,10,15])for(const charge of [0,.5,1])for(const weightKg of [50,95,180]){
  const p=launch({speed,charge,weightKg});assert.ok(p.boost>=0&&p.boost<=1);assert.ok([p.x,p.y,p.spin].every(Number.isFinite));
 }
});

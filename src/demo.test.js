import test from 'node:test';
import assert from 'node:assert/strict';
import {VaultDemo} from './demo.js';
const m={chargeSeconds:.5,age:.6,swingUsed:false,throwUsed:false,swingWindow:1,throwWindow:0};
test('demo uses alternating taps, held Space, timed J and a K tap to throw',()=>{
 const demo=new VaultDemo();demo.start();
 let events=demo.update(.1,{phase:'run',x:-32,frame:1});assert.deepEqual(events,[{key:'KeyD',down:true},{key:'KeyD',down:false}]);
 events=demo.update(.5,{phase:'run',x:-29,frame:1});assert.equal(events[0].key,'KeyL');
 events=demo.update(.1,{phase:'run',x:-18,frame:1});assert.ok(events.some(e=>e.key==='KeyH'&&e.down));
 events=demo.update(.4,{phase:'run',x:-15,frame:49});assert.ok(events.some(e=>e.key==='KeyH'&&!e.down));
 events=demo.update(.1,{phase:'run',x:-12,frame:49});assert.ok(events.some(e=>e.key==='Space'&&e.down));assert.ok(!events.some(e=>e.key==='Space'&&!e.down));
 events=demo.update(.1,{phase:'vault',frame:75,momentum:{...m,age:.1,chargeSeconds:.1,swingWindow:0}});assert.equal(events.length,0);
 events=demo.update(.4,{phase:'vault',frame:121,momentum:m});assert.ok(events.some(e=>e.key==='Space'&&!e.down));assert.ok(events.some(e=>e.key==='KeyJ'&&e.down));
 events=demo.update(.6,{phase:'vault',frame:169,momentum:{...m,swingUsed:true,throwWindow:1}});assert.ok(events.some(e=>e.key==='KeyJ'&&!e.down));assert.deepEqual(events.slice(-2),[{key:'KeyK',down:true},{key:'KeyK',down:false}]);
 demo.reset();assert.deepEqual(demo.update(1,{phase:'run',x:-32}),[]);
});
test('demo restores an interrupted J hold after pause',()=>{
 const demo=new VaultDemo();demo.start();const state={phase:'vault',frame:130,momentum:{...m,swingUsed:true}};demo.update(.1,state);demo.suspend();assert.deepEqual(demo.update(.1,state),[{key:'KeyJ',down:true}]);
});

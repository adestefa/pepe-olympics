import test from 'node:test';
import assert from 'node:assert/strict';
import {AudioEngine} from './audio.js';

const param=()=>({value:0,setValueAtTime(){},exponentialRampToValueAtTime(){}});
class Source {
  constructor(){this.frequency=param();this.stopped=false;this.loop=false;}
  connect(){} disconnect(){} start(){this.started=true;}
  stop(at){if(at===undefined){this.stopped=true;this.onended?.();}}
}
class Context {
  constructor(){this.currentTime=0;this.state='suspended';this.destination={};}
  async resume(){this.state='running';}
  async suspend(){this.state='suspended';}
  async decodeAudioData(){return {};}
  createBufferSource(){return new Source();}
  createOscillator(){return new Source();}
  createGain(){return {gain:param(),connect(){},disconnect(){}};}
}

test('crowd reacts once per round without loops, and mute/reset clear all sources',async t=>{
  const requests=[];
  t.mock.method(globalThis,'fetch',async url=>{requests.push(url);return {ok:true,arrayBuffer:async()=>new ArrayBuffer(0)};});
  globalThis.window={AudioContext:Context,speechSynthesis:{cancel(){}}};
  try{
    const audio=new AudioEngine();await audio.enable();
    assert.equal(audio.sources.size,0,'enabling sound must not start ambience');
    assert.equal(requests.filter(p=>p.includes('crowd-')).length,3);
    assert.ok(!requests.some(p=>p.includes('ambience')));
    audio.roundStart();const applause=audio.crowdSource;
    assert.equal(applause.soundName,'crowd-start');assert.equal(applause.loop,false);
    audio.fail();const failure=audio.crowdSource;
    assert.ok(applause.stopped);assert.equal(failure.soundName,'crowd-failure');
    audio.fail();assert.equal(audio.crowdSource,failure,'crash and landing must not duplicate booing');
    audio.cheer();assert.equal(audio.crowdSource,failure,'failed round cannot also celebrate');
    await audio.ctx.suspend();assert.ok(!failure.stopped,'pause preserves the clip to resume');
    await audio.enable(false);assert.ok(failure.stopped);assert.equal(audio.sources.size,0);
    await audio.enable();assert.equal(audio.sources.size,0,'unmute stays silent until a new event');
    audio.roundStart();audio.cheer();const success=audio.crowdSource;
    assert.equal(success.soundName,'crowd-success');assert.equal(success.loop,false);
    audio.cheer();assert.equal(audio.crowdSource,success);
    audio.tone(80);audio.roundStart();assert.ok(success.stopped);
    assert.deepEqual(audio.snapshot().active,['crowd-start']);assert.equal(audio.outcome,null);
    audio.stopAll();assert.equal(audio.sources.size,0);
  }finally{delete globalThis.window;}
});

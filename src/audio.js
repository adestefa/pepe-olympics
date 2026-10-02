/** Event-driven crowd sounds and short game effects. No background loop. */
const WAV_EFFECTS=['countdown','go','landing','pole-spring','cartoon-crack','reaction','victory'];
const CROWD_EFFECTS=['crowd-start','crowd-failure','crowd-success'];

export class AudioEngine {
  constructor(){
    this.enabled=false;this.ctx=null;this.buffers=new Map();this.sources=new Set();
    this.stepAt=0;this.crowdSource=null;this.crowdEvent=null;this.outcome=null;
  }
  async enable(value=true){
    this.enabled=value;
    if(!value){this.stopAll();return;}
    if(!this.ctx){
      const AC=window.AudioContext||window.webkitAudioContext;
      if(!AC){this.enabled=false;return;}
      this.ctx=new AC();
      this.loading=Promise.all([...WAV_EFFECTS.map(n=>[n,'wav']),...CROWD_EFFECTS.map(n=>[n,'mp3'])].map(async([name,ext])=>{
        try{
          const response=await fetch(`/assets/audio/${name}.${ext}`);
          if(!response.ok)throw Error(response.status);
          this.buffers.set(name,await this.ctx.decodeAudioData(await response.arrayBuffer()));
        }catch(error){console.warn(`Could not load sound ${name}`,error);}
      }));
    }
    await this.ctx.resume();
    await this.loading;
  }
  track(source,gain,name){
    source.soundName=name;this.sources.add(source);
    source.onended=()=>{this.sources.delete(source);source.disconnect();gain.disconnect();if(this.crowdSource===source)this.crowdSource=null;};
    return source;
  }
  stopAll(){
    for(const source of this.sources){try{source.stop();}catch{}}
    this.sources.clear();this.crowdSource=null;
    window.speechSynthesis?.cancel();
  }
  sample(name,volume=.5){
    if(!this.enabled||!this.ctx||!this.buffers.has(name))return;
    const source=this.ctx.createBufferSource(),gain=this.ctx.createGain();
    source.buffer=this.buffers.get(name);source.loop=false;gain.gain.value=volume;
    source.connect(gain);gain.connect(this.ctx.destination);this.track(source,gain,name);source.start();return source;
  }
  tone(frequency,duration=.15,type='sine',volume=.1,slide=0){
    if(!this.enabled||!this.ctx)return;
    const t=this.ctx.currentTime,source=this.ctx.createOscillator(),gain=this.ctx.createGain();
    source.type=type;source.frequency.setValueAtTime(frequency,t);
    if(slide)source.frequency.exponentialRampToValueAtTime(Math.max(30,frequency+slide),t+duration);
    gain.gain.setValueAtTime(volume,t);gain.gain.exponentialRampToValueAtTime(.001,t+duration);
    source.connect(gain);gain.connect(this.ctx.destination);this.track(source,gain,'footstep');source.start();source.stop(t+duration);
  }
  crowd(name,volume){
    if(this.crowdSource){try{this.crowdSource.stop();}catch{}}
    this.crowdEvent=name;this.crowdSource=this.sample(name,volume);
  }
  roundStart(){
    this.stopAll();this.outcome=null;this.crowd('crowd-start',.62);
  }
  fail(){
    if(this.outcome)return;
    this.outcome='failure';this.crowd('crowd-failure',.72);
  }
  cheer(){
    if(this.outcome)return;
    this.outcome='success';this.crowd('crowd-success',.70);this.sample('victory',.35);
  }
  beep(final=false){this.sample(final?'go':'countdown',.55);}
  thud(){this.sample('landing',.6);}
  crack(){this.sample('cartoon-crack',.45);}
  foot(){if(performance.now()-this.stepAt<170)return;this.stepAt=performance.now();this.tone(80,.055,'triangle',.035,-40);}
  boing(){this.sample('pole-spring',.45);}
  say(text,pitch=.7){
    if(!this.enabled||!window.speechSynthesis)return;
    window.speechSynthesis.cancel();const line=new SpeechSynthesisUtterance(text);
    line.pitch=pitch;line.rate=1.2;line.volume=.35;window.speechSynthesis.speak(line);
  }
  snapshot(){return {enabled:this.enabled,state:this.ctx?.state??'uninitialized',crowdEvent:this.crowdEvent,outcome:this.outcome,active:[...this.sources].map(s=>s.soundName),loaded:[...this.buffers.keys()]};}
}

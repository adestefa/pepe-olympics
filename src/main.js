import './style.css';
import {version} from '../package.json';
import * as THREE from 'three';
import {RiggedVaultGame} from './rigged-vault.js';
import {RUN_START,WALL_X,WALL_HEIGHT,MAP_EDGE} from './vault-power.js';
import {VaultDemo} from './demo.js';
import {AudioEngine} from './audio.js';

const $=id=>document.getElementById(id), clamp=THREE.MathUtils.clamp;
$('game-version').textContent='v'+version+' / POLE VAULT';
const physics=new RiggedVaultGame(), audio=new AudioEngine(),demo=new VaultDemo();
const inputKeys=['KeyD','KeyL','KeyH','Space','KeyJ','KeyK'];
const inputState=new Map(inputKeys.map(key=>[key,{down:false,until:0}]));
const renderer=new THREE.WebGLRenderer({canvas:$('game'),antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.22;
const scene=new THREE.Scene();scene.background=new THREE.Color('#dbe5d7');scene.fog=new THREE.Fog('#dbe5d7',35,95);
const camera=new THREE.PerspectiveCamera(38,1,.1,130);
scene.add(new THREE.HemisphereLight('#f9ffe9','#677d52',2.7));
const sun=new THREE.DirectionalLight('#fff0ca',3.6);sun.position.set(-7,17,13);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-26,right:24,top:18,bottom:-18,near:1,far:55});sun.shadow.normalBias=.035;sun.shadow.bias=-.0001;scene.add(sun);scene.add(sun.target);
const fill=new THREE.DirectionalLight('#e5f2ff',1.3);fill.position.set(2,6,-8);scene.add(fill);
const mats={};function material(color,roughness=.8,metalness=0){return mats[color]??=new THREE.MeshStandardMaterial({color,roughness,metalness});}
function box(x,y,z,w,h,d,color,shadow=true){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material(color));m.position.set(x,y,z);m.receiveShadow=true;m.castShadow=shadow;scene.add(m);return m;}
function cylinder(a,b,r,color,segments=12){const d=new THREE.Vector3().subVectors(b,a);const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,d.length(),segments),material(color));m.position.copy(a).addScaledVector(d,.5);m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());m.castShadow=true;scene.add(m);return m;}
function textPlane(text,width,height,{bg='#213a31',fg='#e8edca',font='bold 62px Arial',resolution=1024}={}){const c=document.createElement('canvas');c.width=resolution;c.height=Math.round(resolution*height/width);const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle=fg;ctx.font=font;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,c.width/2,c.height/2,c.width*.91);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(width,height),new THREE.MeshBasicMaterial({map:t,side:THREE.DoubleSide}));scene.add(m);return m;}

// A small, fully modeled practice stadium.
box(-1,-.21,0,110,.4,85,'#a6b793',false);
box(-8,-.045,0,64,.1,8.2,'#b77452',false);
box(-8,.008,0,64,.012,3.7,'#be8060',false);
for(const z of [-3.65,-1.88,1.88,3.65])box(-8,.019,z,64,.015,.045,'#e9d5b2',false);
for(let x=-38;x<24;x+=2){box(x,.026,1.78,.035,.016,.20,'#edddba',false);box(x,.026,-1.78,.035,.016,.20,'#edddba',false);}
for(let i=0;i<6;i++){const t=textPlane(String(6-i),.7,.5,{bg:'#b77452',fg:'#f2dfb7',font:'bold 110px Arial',resolution:256});t.rotation.x=-Math.PI/2;t.position.set(-15+i*3,.027,2.8);}
const groundPlant=box(.9,.045,0,.38,.04,.44,'#d5e88a',false);groundPlant.visible=false;
const plantZone=box(-3.65,.033,0,1.8,.02,3.65,'#c6df79',false);
box(.9,.028,0,.38,.06,.44,'#52624c',false);
const plantText=textPlane('REFERENCE  ↑',2.0,.29,{bg:'#c6df79',fg:'#415936',font:'bold 74px Arial'});plantText.rotation.x=-Math.PI/2;plantText.position.set(-3.65,.048,1.38);
// A real distant collision wall turns overpowered vaults into slapstick.
box(WALL_X,WALL_HEIGHT/2,0,.8,WALL_HEIGHT,9,'#657765');
for(let y=.5;y<WALL_HEIGHT;y+=1)box(WALL_X-.412,y,0,.025,.035,8.9,'#93a28c',false);
const wallSign=textPlane('DEFINITELY SOFT',6.5,1.2,{bg:'#e2c687',fg:'#314c3d',font:'bold 82px Arial'});wallSign.rotation.y=-Math.PI/2;wallSign.position.set(WALL_X-.42,4.4,0);
const startLine=box(RUN_START,.033,0,.08,.02,3.65,'#e9d5b2',false);
const runwayLabel=textPlane('LONG RUN. BAD IDEAS.',6,.6,{bg:'#be8060',fg:'#f1dfb5',font:'bold 78px Arial'});runwayLabel.rotation.x=-Math.PI/2;runwayLabel.position.set(-29,.04,2.8);
// Layered landing pads and stitched top panels.
box(6.5,.14,0,7.3,.28,5.05,'#344f45');box(6.5,.44,0,7.2,.52,5,'#6d9676');
for(let i=0;i<3;i++)for(let j=0;j<2;j++)box(4.12+i*2.4,.74,-1.25+j*2.5,2.34,.10,2.43,'#91ae88');
const matLogo=textPlane('SOFT LANDINGS CLUB',5,.47,{bg:'#6d9676',fg:'#d8e9be',font:'bold 56px Arial'});matLogo.position.set(6.5,.45,2.512);
const topLogo=textPlane('p ↗',1.7,1.1,{bg:'#91ae88',fg:'#d6e5b6',font:'bold italic 125px Georgia'});topLogo.rotation.x=-Math.PI/2;topLogo.position.set(6.5,.802,0);
const barSupports=[];
for(const z of [-2.1,2.1]){
  box(2.3,.1,z,1,.2,.7,'#2e473d');box(2.3,3,z,.09,6,.09,'#e4e6cc');box(2.3,3,z+.07,.06,5.9,.045,'#657c6b');
  for(let y=1;y<=6;y+=.2)box(2.36,y,z+.052,.05,.025,.02,y%1<.05?'#384c40':'#81907a',false);
  const support=box(2.2,4.15,z,.4,.07,.16,'#d8ed9a');barSupports.push(support);
  const flag=textPlane('PEPE / ATHLETICS',.48,1.65,{bg:'#d3e792',fg:'#354d38',font:'bold 32px Arial',resolution:256});flag.position.set(2.3,3.25,z+.09);
}
let barVisual=new THREE.Group();scene.add(barVisual);
// Bar is visible even before asset loads.
const barMesh=new THREE.Mesh(new THREE.CylinderGeometry(.045,.045,4.1,16),material('#d7ed88'));barMesh.rotation.x=Math.PI/2;barMesh.castShadow=true;barVisual.add(barMesh);
for(const z of [-1.75,-1.5,1.5,1.75]){const tape=new THREE.Mesh(new THREE.CylinderGeometry(.048,.048,.12,12),material('#f5edc7'));tape.rotation.x=Math.PI/2;tape.position.z=z;barVisual.add(tape);}
// Trackside boards and seating, deliberately graphic and low in the background.
box(-1,.63,-6.4,39,1.25,.22,'#48604b');
for(const [x,text,bg,fg] of [[-15,'THE QUESTIONABLE GAMES','#d6dfb6','#435b42'],[-7.2,'NO PAIN. NO MEME.','#355341','#e5edc9'],[.6,'PEPE ATHLETICS  ↗','#d6dfb6','#435b42'],[8.4,'GRAVITY ALWAYS WINS.','#355341','#e5edc9']]){const m=textPlane(text,7.5,1.04,{bg,fg,font:'bold 57px Arial'});m.position.set(x,.67,-6.265);}
for(let row=0;row<5;row++){
  box(-2,.7+row*.43,-8.1-row*.86,44,.40,1.0,row%2?'#abb99a':'#b8c4a7');
  box(-2,1+row*.43,-8.45-row*.86,44,.06,.13,'#718465');
}
let seed=123;const rand=()=>{seed=(seed*16807)%2147483647;return(seed-1)/2147483646;};
const crowdCount=420,crowd=new THREE.InstancedMesh(new THREE.CapsuleGeometry(.10,.22,3,6),new THREE.MeshStandardMaterial({roughness:1}),crowdCount),heads=new THREE.InstancedMesh(new THREE.SphereGeometry(.09,7,5),material('#ac9a71'),crowdCount);const dummy=new THREE.Object3D();const crowdColors=['#304e40','#769061','#ddd3a7','#99a681','#627252','#c19c6b','#a9b590'];
for(let i=0;i<crowdCount;i++){const row=Math.floor(i/84),x=-23+(i%84)*.51+rand()*.16,y=1.06+row*.43,z=-8.2-row*.86;dummy.position.set(x,y,z);dummy.scale.set(1,1+rand()*.25,1);dummy.updateMatrix();crowd.setMatrixAt(i,dummy.matrix);crowd.setColorAt(i,new THREE.Color(crowdColors[Math.floor(rand()*crowdColors.length)]));dummy.position.y+=.27;dummy.scale.setScalar(1);dummy.updateMatrix();heads.setMatrixAt(i,dummy.matrix);}scene.add(crowd,heads);
box(-2,3.15,-13.2,47,.15,.16,'#87997b');
for(let x=-24;x<23;x+=4)box(x,1.8,-13.2,.045,2.7,.045,'#87997b');
// Scoreboard and flag poles.
box(11,5.0,-11,5,2.8,.25,'#253d33');const board=textPlane('PEPE  /  069',4.6,.58,{bg:'#253d33',fg:'#cde685',font:'bold 80px Arial'});board.position.set(11,5.72,-10.86);
const board2=textPlane('POLE VAULT     4.20 m',4.6,1,{bg:'#253d33',fg:'#e7ecd2',font:'bold 70px monospace'});board2.position.set(11,4.65,-10.86);
for(const x of [9.3,12.7])box(x,2.2,-11,.09,4.2,.09,'#5e775e');
for(const x of [-15,-7,1,18]){box(x,4.3,-14.2,.055,8.6,.055,'#7d9276');const flag=textPlane(x===1?'P ↗':'PEPE',1.5,.85,{bg:x===-7?'#eff0cc':'#91a967',fg:'#3a553a',font:'bold italic 170px Arial',resolution:512});flag.position.set(x+.73,7.6,-14.2);}
for(let i=0;i<25;i++){const x=-43+i*3.6,z=-19-rand()*8;const m=new THREE.Mesh(new THREE.IcosahedronGeometry(1.3+rand()*1.4,1),material(i%2?'#99ae89':'#a4b696'));m.scale.y=1.6;m.position.set(x,3.1,z);scene.add(m);}
// World markers and foreground details.
for(const x of [-18,-10,0]){const cone=new THREE.Mesh(new THREE.ConeGeometry(.17,.46,16),material('#e3a15e'));cone.position.set(x,.23,4.4);scene.add(cone);box(x,.03,4.4,.40,.06,.40,'#e1a76e');}
let loaded=false,paused=false,uiState='intro',count=0,countTime=0,lastPhase='',resultDelay=0,runHeld=false,raiseHeld=false,tuckHeld=false,swingHeld=false,chargeHeld=false,best=0;
try{best=Number(localStorage.getItem('pepe-best')||0);}catch{}
function updateBest(){ $('best-label').innerHTML=(best?best.toFixed(2):'—')+'<small>m</small>'; }updateBest();
physics.load(scene).then(()=>{loaded=true;$('start').disabled=false;$('demo-start').disabled=false;$('start-label').textContent='LET’S VAULT';}).catch(error=>{console.error(error);$('start-label').textContent='MODEL FAILED TO LOAD';$('intro').insertAdjacentHTML('beforeend','<p class="loading-error">Try reloading. Serve the project with npm run dev.</p>');});

function resize(){const w=$('viewport').clientWidth,h=$('viewport').clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe($('viewport'));resize();
function setHeight(){physics.height=Number($('height').value);$('height-value').textContent=physics.height.toFixed(2)+' m';$('bar-label').innerHTML=physics.height.toFixed(2)+'<small>m</small>';physics.setBarHeight(physics.height);for(const b of barSupports)b.position.y=physics.height-.05;const c=board2.material.map.image,ctx=c.getContext('2d');ctx.fillStyle='#253d33';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#e7ecd2';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='bold 70px monospace';ctx.fillText('POLE VAULT     '+physics.height.toFixed(2)+' m',c.width/2,c.height/2,c.width*.91);board2.material.map.needsUpdate=true;} $('height').addEventListener('input',setHeight);setHeight();
function setWeight(){physics.setWeight(Number($('weight').value));$('weight-value').textContent=physics.weightKg+' kg';$('athlete-weight').textContent=physics.weightKg+' KG · QUESTIONABLE JUDGEMENT';}
$('weight').addEventListener('input',setWeight);setWeight();
function hide(id,value=true){$(id).classList.toggle('hidden',value);}
function reset(){demo.reset();clearInputs();hide('key-coach');audio.stopAll();runHeld=false;raiseHeld=false;tuckHeld=false;swingHeld=false;chargeHeld=false;paused=false;$('pause').textContent='Ⅱ';physics.reset(-3.9,'preview');setHeight();uiState='intro';hide('intro',false);hide('result');hide('countdown');hide('speech');hide('play-hud');hide('touch-controls');$('height').disabled=false;$('weight').disabled=false;resultDelay=0;audio.ctx?.resume();}
async function start(demonstration=false){if(!loaded)return;demo.reset();clearInputs();if(demonstration)demo.start();hide('key-coach',false);$('coach-mode').textContent=demonstration?'DEMO · WATCH THE KEYS':'YOUR INPUTS';hide('demo-exit',!demonstration);runHeld=false;raiseHeld=false;tuckHeld=false;swingHeld=false;chargeHeld=false;if(!audio.ctx)await audio.enable(true);else if(audio.enabled)await audio.ctx.resume();updateSound();physics.reset(RUN_START,'ready');setHeight();uiState='countdown';count=3;countTime=0;hide('intro');hide('result');hide('countdown',false);$('countdown').textContent='3';hide('speech');hide('play-hud',false);hide('touch-controls',false);$('height').disabled=true;$('weight').disabled=true;$('viewport').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});audio.roundStart();audio.beep();resultDelay=0;paused=false;$('pause').textContent='Ⅱ';}
$('start').onclick=()=>start();$('retry').onclick=()=>start();$('demo-start').onclick=()=>start(true);$('reset').onclick=reset;
$('demo-exit').onclick=()=>takeControl();
function updateSound(){$('sound').innerHTML='♪ <span>SOUND '+(audio.enabled?'ON':'OFF')+'</span>';$('sound').setAttribute('aria-label',audio.enabled?'Mute sound':'Enable sound');}
$('sound').onclick=async()=>{await audio.enable(!audio.enabled);if(paused)audio.ctx?.suspend();updateSound();};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('viewport').requestFullscreen();}catch{}};
function pause(value){paused=value;clearInputs();demo.suspend();runHeld=false;raiseHeld=false;tuckHeld=false;swingHeld=false;chargeHeld=false;hide('countdown',!value);$('countdown').textContent=value?'PAUSED':(uiState==='countdown'?String(count):'');$('pause').textContent=value?'▶':'Ⅱ';$('pause').setAttribute('aria-label',value?'Resume game and sounds':'Pause game and sounds');if(!value&&uiState==='countdown')hide('countdown',false);if(value){audio.ctx?.suspend();window.speechSynthesis?.cancel();}else audio.ctx?.resume();}
$('pause').onclick=()=>pause(!paused);let guideWasPaused=false;
$('guide-open').onclick=()=>{guideWasPaused=paused;pause(true);$('guide').showModal();};$('guide-close').onclick=()=>$('guide').close();$('guide').addEventListener('close',()=>pause(guideWasPaused));$('arena-tab').onclick=()=>$('viewport').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});
function jump(){if(uiState!=='playing'||paused)return;if(physics.phase==='run'){physics.plant();if(physics.phase==='vault')audio.boing();}}
function clearInputs(){
  for(const state of inputState.values()){state.down=false;state.until=0;}
  raiseHeld=false;swingHeld=false;chargeHeld=false;
}
function takeControl(){demo.reset();clearInputs();$('coach-mode').textContent='YOUR INPUTS';hide('demo-exit');}
function input(key,down,fromDemo=false){
  if(!inputState.has(key))return;
  if(!fromDemo&&down&&demo.active)takeControl();
  const state=inputState.get(key),fresh=down&&!state.down;
  state.down=down;
  if(down)state.until=physics.time+.16;
  if(paused||uiState!=='playing')return;
  if(fresh&&['KeyD','KeyL'].includes(key)){if(physics.stepFoot(key==='KeyD'?'left':'right'))audio.foot();}
  if(key==='KeyH'){raiseHeld=down;if(fresh)physics.motion.lowerPoleTap();}
  if(key==='KeyJ'){swingHeld=down;if(fresh)physics.swing();}
  if(key==='KeyK'&&fresh)physics.throw();
  if(key==='Space'){chargeHeld=down;if(fresh)jump();}
}
window.addEventListener('keydown',e=>{
  if($('guide').open)return;
  if(e.code==='Space'&&uiState==='intro')return;
  if(inputKeys.includes(e.code))e.preventDefault();
  if(e.repeat)return;
  if(e.code==='KeyR'){reset();return;}
  if(['Escape','KeyP'].includes(e.code)){pause(!paused);return;}
  input(e.code,true);
});
window.addEventListener('keyup',e=>input(e.code,false));
window.addEventListener('blur',()=>pause(true));document.addEventListener('visibilitychange',()=>{if(document.hidden)pause(true);});
for(const [id,key] of [['left-touch','KeyD'],['right-touch','KeyL'],['lift-touch','KeyH'],['jump-touch','Space'],['swing-touch','KeyJ'],['invert-touch','KeyK']]){
 const button=$(id);button.onpointerdown=e=>{e.preventDefault();button.setPointerCapture(e.pointerId);input(key,true);};
 button.onpointerup=button.onpointercancel=button.onlostpointercapture=()=>input(key,false);
}
function updateCoach(){
  $('coach-caption').textContent=demo.active?demo.caption:'HOLD Space to charge · TIME J, then TAP K';
  for(const key of inputKeys){
    const state=inputState.get(key),active=state.down||physics.time<state.until;
    const tile=document.querySelector(`[data-key="${key}"]`);tile.classList.toggle('active',active);
    tile.classList.toggle('holding',active&&['KeyH','KeyJ','Space'].includes(key));
    tile.querySelector('em').textContent=active?(['KeyH','KeyJ','Space'].includes(key)&&state.down?'HOLDING':'TAP!'):['KeyH','Space'].includes(key)?'TAP / HOLD':key==='KeyJ'?'TIME + HOLD':'TAP';
    const id={KeyD:'left-touch',KeyL:'right-touch',KeyH:'lift-touch',Space:'jump-touch',KeyJ:'swing-touch',KeyK:'invert-touch'}[key];$(id).classList.toggle('pressed',active);
  }
}
function showResult(){const r=physics.result;if(!r)return;uiState='result';hide('result',false);hide('play-hud');hide('touch-controls');hide('speech');$('height').disabled=false;$('weight').disabled=false;$('result-kicker').textContent=r.clean?'AGAINST ALL MEDICAL ADVICE':'THAT’S GOING ON THE BLOOPER REEL';$('result-title').textContent=r.clean?'A frog. A flight. A legend.':'Gravity: 1. Pepe: 0.';$('result-copy').textContent=r.reason+(r.distance>12?' Flight distance: '+r.distance.toFixed(1)+' m.':'');$('result-height').textContent=r.height.toFixed(2)+' m';$('result-review').textContent=r.review;if(r.clean&&!demo.active){best=Math.max(best,r.height);try{localStorage.setItem('pepe-best',best);}catch{}updateBest();}}
const target=new THREE.Vector3(),camPos=new THREE.Vector3();let previous=performance.now();let elapsed=0;
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-previous)/1000,1/30);previous=now;if(!paused){elapsed+=dt;
  if(uiState==='countdown'){countTime+=dt;if(countTime>=1){countTime=0;count--;if(count>0){$('countdown').textContent=count;audio.beep();}else{uiState='playing';physics.phase='run';physics.phaseTime=0;hide('countdown');audio.beep(true);}}}
  if(demo.active&&uiState==='playing')for(const e of demo.update(dt,physics.snapshot()))input(e.key,e.down,true);
  if(loaded)physics.update(dt,{run:uiState==='playing'&&runHeld,tuck:tuckHeld,raise:raiseHeld,swing:swingHeld,charge:chargeHeld});
  if(uiState==='playing'){
    const speed=Math.max(0,physics.ragdoll?physics.bodies.hips.velocity.x:physics.speed);$('left-key').classList.toggle('pressed',physics.time-physics.footTimes.left<.2);$('right-key').classList.toggle('pressed',physics.time-physics.footTimes.right<.2);$('speed').textContent=speed.toFixed(1);$('speed-fill').style.width=clamp(speed/13*100,0,100)+'%';$('speed-fill').style.background=speed>10?'#cf744b':'#84a950';
    const lift=physics.poleLift;$('lift-fill').style.width=(lift*100)+'%';$('lift-fill').style.background=lift>.75?'#cf744b':lift>.4?'#c2aa4e':'#84a950';$('lift-status').textContent=lift>.75?'HANDS READY':lift>.4?'LOWERING POLE':'TAP / HOLD H TO LOWER';$('lift-key').classList.toggle('pressed',raiseHeld);
    const zone=Math.abs(physics.bodies.hips.position.x+3.65)<.9;
    const m=physics.momentum, onPole=physics.phase==='vault';
    let timing='SPACE · PLANT + HOLD TO CHARGE', readiness=0;
    if(onPole){
      readiness=m.swingUsed?m.throwWindow:m.swingWindow;
      timing=m.throwUsed?'THROWING · KEEP SPACE HELD FOR POWER':!m.swingUsed?(m.swingWindow>.72?'J NOW · HOLD TO SWING':'WAIT FOR THE SURGE · THEN J'):physics.motion.frame<165?'KEEP HOLDING J · FEET UP':m.throwWindow>.7?'K NOW · TAP TO THROW':'K · TAP TO THROW';
    }
    $('charge-fill').style.width=m.charge*100+'%';$('charge-value').textContent=Math.round(m.charge*100)+'%';
    $('timing-fill').style.width=readiness*100+'%';$('timing-fill').classList.toggle('ready',readiness>.7);
    $('timing-cue').textContent=timing;$('timing-cue').classList.toggle('ready',onPole&&readiness>.7);
    $('phase-label').textContent=physics.phase==='run'?(zone?'CLASSIC PLANT ZONE':(speed>10?'DANGEROUS AMOUNT OF SPEED':lift>.75?'HANDS READY · KEEP STEPPING':'BUILD YOUR SPEED')):onPole?(m.throwUsed?'TURNING MOMENTUM INTO FLIGHT':m.swingUsed?m.feedback:'FORWARD MOMENTUM · TIME YOUR SWING'):physics.phase==='flight'?(physics.launchBoost>.4?'THE MAT IS GETTING SMALLER':'LET IT FLY'):'PLEASE REMAIN IN ONE PIECE';
    $('hint').textContent=physics.phase==='run'?'SPACE · PLANT HERE · '+Math.max(0,2.3-physics.bodies.hips.position.x).toFixed(1)+' m TO BAR':onPole?'Hold SPACE longer = more height · K lets go':physics.phase==='flight'?'Aim for the mat. Gravity has it from here.':'Gravity has the controls now.';
    plantZone.material.emissive.set(zone&&physics.phase==='run'?'#507416':'#000000');

    if(physics.barHit||physics.wallHit||physics.outOfBounds)audio.fail();
    if(physics.phase==='crash'&&lastPhase!=='crash'){audio.fail();audio.thud();audio.say('Oh no no no no!',1.0);$('speech').textContent=['MY EVERYTHING!','THIS SEEMED EASIER ONLINE.','I REGRET THE LEG DAY.'][Math.floor(Math.random()*3)];hide('speech',false);}
    if(physics.result){if(resultDelay===0){audio.thud();if(physics.breakName)audio.crack();if(physics.result.clean)audio.cheer();else audio.fail();}resultDelay+=dt;if(resultDelay>1.65)showResult();}
  }
  if(uiState!=='intro')updateCoach();
  lastPhase=physics.phase;
}
  groundPlant.visible=physics.anchorX!==null;if(groundPlant.visible)groundPlant.position.x=physics.anchorX;
  barVisual.position.copy(physics.bar.position);barVisual.quaternion.copy(physics.bar.quaternion);
  // Trackside camera follows the controlled technique and physical flight.
  const mobile=camera.aspect<1.1;let tx,ty,distance;
  if(uiState==='intro'){tx=mobile?-3.0:-2;ty=mobile?2.0:1.65;distance=mobile?20:15.5;}
  else {tx=clamp(physics.bodies.hips.position.x+3,RUN_START,MAP_EDGE+3);ty=Math.max(1.6,physics.bodies.hips.position.y*.82);distance=(mobile?24:18.5)+physics.launchBoost*6;}
  target.set(tx,ty,0);camPos.set(tx+distance*.34,ty+distance*.28,distance);camera.position.lerp(camPos,1-Math.exp(-dt*(physics.ragdoll?7:5)));camera.lookAt(target);
  renderer.render(scene,camera);
}
camera.position.set(5,9,25);requestAnimationFrame(animate);
// Read-only diagnostics used by browser smoke checks; gameplay is controlled through the UI.
window.pepeDebug={snapshot:()=>({...physics.snapshot(),uiState,loaded,paused,audio:audio.enabled,demo:demo.active,keys:Object.fromEntries([...inputState].map(([k,v])=>[k,v.down||physics.time<v.until]))}),audioState:()=>audio.ctx?.state??'uninitialized',sound:()=>audio.snapshot(),renderer:()=>({calls:renderer.info.render.calls,triangles:renderer.info.render.triangles})};

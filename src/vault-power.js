// Arcade energy transfer with a continuous incoming velocity, not a fixed jump.
export const RUN_START=-32;
export const WALL_X=27;
export const WALL_HEIGHT=7;
export const MAP_EDGE=54;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export function launchPower({speed,quality,charge,swingTiming,throwTiming,velocity,weightKg=95}){
  const pace=clamp((speed-3.2)/9.8,0,1),spring=clamp(charge,0,1);
  const timing=(.15+.85*clamp(swingTiming,0,1))*(.15+.85*clamp(throwTiming,0,1));
  const forceScale=Math.sqrt(95/clamp(weightKg,50,180));
  const drive=pace*clamp(quality,0,1)*(.25+.75*timing);
  return {
    boost:clamp(drive+spring*.5+timing*.15,0,1),
    x:Math.max(1.5,clamp(velocity.x,-8,18)*.7+speed*.5+(3+drive*24+spring*3*timing)*forceScale),
    y:Math.max(1.8,clamp(velocity.y,-8,16)*.4)+(3.2+drive*6+spring*12+timing*2.5)*forceScale,
    spin:1.7+drive*1.2+(1-timing)*2.0,
  };
}

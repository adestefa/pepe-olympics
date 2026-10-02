async () => {
  const {Vector3, Quaternion} = await import('/node_modules/three/build/three.module.js');
  const {constrainJointRotation} = await import('/src/joint-limits.js');
  const limits = await fetch('/assets/pepe-joint-limits.json').then(r=>r.json());
  const s = window.plantStudy;
  if (!s) throw Error('Study did not load');
  const {model, report, seek, action} = s;
  const meshes = [], rigs = new Map();
  model.traverse(o=>{if(o.isSkinnedMesh){meshes.push(o);rigs.set(o.skeleton.uuid,o.skeleton.bones.length)}});
  const point = name => model.getObjectByName(name).getWorldPosition(new Vector3());
  const gripBind = {}, bindRotation = {}, clampMax = {};
  seek(1); model.updateMatrixWorld(true);
  for (const side of ['Right','Left']) gripBind[side] = model.getObjectByName(side+'_hand').worldToLocal(point('GripSocket_'+side));
  for (const [name,limit] of Object.entries(limits.joints)) bindRotation[name] = new Quaternion().fromArray(limit.bind_local_rotation_xyzw);
  seek(73); model.updateMatrixWorld(true);
  const anchor = point('PoleFlex_20');
  let maxGripError = 0, maxAnchorError = 0, maxWrist = 0, checkedVertices = 0, minHeight=Infinity;
  for (let frame=1;frame<=report.frames;frame++) {
    seek(frame); model.updateMatrixWorld(true);
    for (const side of ['Right','Left']) {
      const hand=model.getObjectByName(side+'_hand'), fore=model.getObjectByName(side+'_forearm_twist');
      maxGripError=Math.max(maxGripError,hand.localToWorld(gripBind[side].clone()).distanceTo(point('GripSocket_'+side)));
      const a=new Vector3(0,1,0).applyQuaternion(hand.getWorldQuaternion(new Quaternion()));
      const b=new Vector3(0,1,0).applyQuaternion(fore.getWorldQuaternion(new Quaternion()));
      maxWrist=Math.max(maxWrist,a.angleTo(b)*180/Math.PI);
    }
    if(frame>=73) maxAnchorError=Math.max(maxAnchorError,anchor.distanceTo(point('PoleFlex_20')));
    for(const [name,limit] of Object.entries(limits.joints)) {
      const delta=bindRotation[name].clone().invert().multiply(model.getObjectByName(name).quaternion);
      const change=delta.angleTo(constrainJointRotation(delta,limit))*180/Math.PI;
      clampMax[name]=Math.max(clampMax[name]??0,change);
    }
    for (const mesh of meshes) {
      mesh.skeleton.update();
      for(let i=0;i<mesh.geometry.attributes.position.count;i+=47) {
        const p=mesh.getVertexPosition(i,new Vector3()).applyMatrix4(mesh.matrixWorld);
        if(![p.x,p.y,p.z].every(Number.isFinite)||p.length()>4) throw Error(`Invalid skin at frame ${frame}`);
        minHeight=Math.min(minHeight,p.y);checkedVertices++;
      }
    }
  }
  const result={frames:report.frames,clip:action.getClip().name,duration:action.getClip().duration,rigBoneCounts:[...rigs.values()],maxGripError,maxAnchorError,maxWrist,checkedVertices,minHeight,clampMax};
  seek(193);model.updateMatrixWorld(true);const headHeight=point('head').y;result.feetAboveHead=Object.fromEntries(['Right','Left'].map(side=>[side,point(side+'_foot').y-headHeight]));if(Math.min(...Object.values(result.feetAboveHead))<.35)throw Error('Inversion does not lift both feet above head');
  if(maxGripError>.002||maxAnchorError>.0001||maxWrist>35||Math.max(...Object.values(clampMax))>.1) throw Error(JSON.stringify(result));
  return result;
}

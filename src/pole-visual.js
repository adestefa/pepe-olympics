import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

// Skin the Blender pole to the existing nine simulated flex sections.
// Blender asset: butt at Y=0. Physics: planting tip at section 0.
export async function loadPoleVisual(scene) {
  const {scene: source} = await new GLTFLoader().loadAsync('/assets/vault-pole.glb');
  source.updateMatrixWorld(true);
  const root = new THREE.Group();
  root.name = 'PhysicsDrivenVaultPole';
  const bones = Array.from({length: 9}, (_, i) => {
    const bone = new THREE.Bone();
    bone.position.y = (i + .5) * .62;
    root.add(bone);
    return bone;
  });
  scene.add(root);
  root.updateMatrixWorld(true);
  const skeleton = new THREE.Skeleton(bones);
  const scale = 5.58 / 1.95;
  source.traverse(object => {
    if (!object.isMesh) return;
    const geometry = object.geometry.clone();
    geometry.applyMatrix4(object.matrixWorld);
    geometry.scale(scale, scale, scale);
    geometry.rotateX(Math.PI);
    geometry.translate(0, 5.58, 0);
    const positions = geometry.attributes.position;
    const indices = new Uint16Array(positions.count * 4);
    const weights = new Float32Array(positions.count * 4);
    for (let i = 0; i < positions.count; i++) {
      const along = THREE.MathUtils.clamp(positions.getY(i) / .62 - .5, 0, 8);
      const lo = Math.floor(along), hi = Math.min(8, lo + 1), mix = along - lo;
      indices[i * 4] = lo; indices[i * 4 + 1] = hi;
      weights[i * 4] = 1 - mix; weights[i * 4 + 1] = mix;
    }
    geometry.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(indices, 4));
    geometry.setAttribute('skinWeight', new THREE.Float32BufferAttribute(weights, 4));
    const mesh = new THREE.SkinnedMesh(geometry, object.material);
    mesh.name = object.name;
    mesh.frustumCulled = false;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    root.add(mesh);
    mesh.bind(skeleton, new THREE.Matrix4());
  });
  return {
    root,
    update(bodies) {
      for (let i = 0; i < bones.length; i++) {
        bones[i].position.copy(bodies[i].position);
        bones[i].quaternion.copy(bodies[i].quaternion);
      }
    },
  };
}

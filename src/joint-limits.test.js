import test from 'node:test';
import assert from 'node:assert/strict';
import {Quaternion, Vector3, MathUtils} from 'three';
import {constrainJointRotation} from './joint-limits.js';
const q = (axis, degrees) => new Quaternion().setFromAxisAngle(new Vector3(...axis), MathUtils.degToRad(degrees));
const same = (a, b) => assert.ok(a.angleTo(b) < 1e-6);
test('elbow converts anatomical bend to the carry bind and locks off-axis rotation', () => {
  const limits = {type:'hinge', bend:[3,148], bind_bend_degrees:108};
  same(constrainJointRotation(q([1,0,0],70),limits),q([1,0,0],40));
  same(constrainJointRotation(q([1,0,0],-150),limits),q([1,0,0],-105));
  same(constrainJointRotation(q([0,1,0],25),limits),new Quaternion());
});
test('wrist independently restricts swing and twist', () => {
  const limits={type:'swing_twist',swing_cone:35,axial_twist:[-20,20]};
  const input=q([1,0,0],70).multiply(q([0,1,0],55));
  same(constrainJointRotation(input,limits),q([1,0,0],35).multiply(q([0,1,0],20)));
});
test('allowed poses and opposite quaternion signs remain equivalent', () => {
  const limits={type:'swing_twist',swing_cone:35,axial_twist:[-20,20]};
  const input=q([1,0,0],10).multiply(q([0,1,0],-5));
  same(constrainJointRotation(input,limits),input);
  const opposite=new Quaternion(-input.x,-input.y,-input.z,-input.w);
  same(constrainJointRotation(opposite,limits),input);
});
test('forearm neutral offset handles the 180-degree quaternion wrap', () => {
  const limits={type:'axial_twist',twist:[-115,115],neutral_twist_from_bind_degrees:-106};
  same(constrainJointRotation(q([0,1,0],148),limits),q([0,1,0],-212));
  same(constrainJointRotation(q([0,1,0],40),limits),q([0,1,0],9));
});

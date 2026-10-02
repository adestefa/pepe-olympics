import {Quaternion, Vector3, MathUtils} from 'three';

const X = new Vector3(1, 0, 0), Y = new Vector3(0, 1, 0);
const radians = MathUtils.degToRad;
const wrap = angle => Math.atan2(Math.sin(angle), Math.cos(angle));

function twistOf(rotation, axis) {
  const projection = rotation.x * axis.x + rotation.y * axis.y + rotation.z * axis.z;
  const twist = new Quaternion(axis.x * projection, axis.y * projection, axis.z * projection, rotation.w);
  return twist.lengthSq() < 1e-12 ? twist.identity() : twist.normalize();
}

function clampTwist(twist, axis, range, neutral = 0) {
  const along = twist.x * axis.x + twist.y * axis.y + twist.z * axis.z;
  const center = radians(neutral);
  const angle = center + wrap(2 * Math.atan2(along, twist.w) - center);
  const bounded = MathUtils.clamp(angle, center + radians(range[0]), center + radians(range[1]));
  return new Quaternion().setFromAxisAngle(axis, bounded);
}

/**
 * Constrain a joint's quaternion DELTA from its exported bind orientation.
 * Apply this in the correct parent/bind frame before driving a bone or a physics
 * motor. It does not create Cannon constraints or overwrite live body poses.
 * Hinge bend bounds are anatomical bend angles; bind_bend_degrees converts them
 * to local deltas. Other bounds are centered on the configured neutral twist.
 */
export function constrainJointRotation(rotation, limit, out = new Quaternion()) {
  const q = rotation.clone().normalize();
  if (limit.type === 'hinge') {
    const bind = limit.bind_bend_degrees ?? 0;
    const range = limit.bend.map(angle => angle - bind);
    return out.copy(clampTwist(twistOf(q, X), X, range));
  }
  if (limit.type === 'axial_twist') {
    return out.copy(clampTwist(twistOf(q, Y), Y, limit.twist, limit.neutral_twist_from_bind_degrees ?? 0));
  }
  if (!['cone_twist', 'swing_twist'].includes(limit.type)) {
    throw new Error(`Unsupported joint limit type: ${limit.type}`);
  }
  const twist = twistOf(q, Y);
  const swing = q.clone().multiply(twist.clone().invert()).normalize();
  if (swing.w < 0) swing.set(-swing.x, -swing.y, -swing.z, -swing.w);
  const angle = 2 * Math.acos(MathUtils.clamp(swing.w, -1, 1));
  const cone = radians(limit.swing_cone ?? 180);
  if (angle > cone) swing.slerp(new Quaternion(), 1 - cone / angle);
  const boundedTwist = clampTwist(twist, Y, limit.twist ?? limit.axial_twist ?? [-180, 180], limit.neutral_twist_from_bind_degrees ?? 0);
  return out.copy(swing).multiply(boundedTwist).normalize();
}

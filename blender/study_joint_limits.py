"""Center shoulder/ankle edit envelopes on the reviewed clip's local bind frame."""
import math
import numpy as np
from mathutils import Quaternion

def calibrate_limits(scene, rig, limits):
    for side in ['Right', 'Left']:
        for part in ['upper_arm', 'foot']:
            name = side + '_' + part
            entry = limits['joints'][name]
            twists, swings = [], []
            for frame in range(scene.frame_start, scene.frame_end + 1):
                scene.frame_set(frame)
                q = rig.pose.bones[name].matrix_basis.to_quaternion().normalized()
                twist = Quaternion((q.w, 0, q.y, 0))
                if twist.magnitude < 1e-8: twist = Quaternion()
                else: twist.normalize()
                swing = q @ twist.inverted()
                swings.append(math.degrees(2 * math.acos(min(1, abs(swing.w)))))
                twists.append(2 * math.atan2(twist.y, twist.w))
            values = np.degrees(np.unwrap(twists))
            lo, hi = float(min(values)), float(max(values))
            key = 'twist' if part == 'upper_arm' else 'axial_twist'
            minimum = 110 if part == 'upper_arm' else 15
            half = max(minimum, math.ceil(((hi - lo) / 2 + 5) / 5) * 5)
            entry[key] = [-half, half]
            entry['neutral_twist_from_bind_degrees'] = (lo + hi) / 2
            entry['observed_twist_from_bind_degrees'] = [lo, hi]
            entry['observed_swing_degrees'] = max(swings)
            entry['swing_cone'] = max(entry['swing_cone'], math.ceil((max(swings) + 5) / 5) * 5)
            bone = rig.pose.bones[name]
            bone['game_' + key] = entry[key]
            bone['game_neutral_twist_from_bind_degrees'] = entry['neutral_twist_from_bind_degrees']
            bone['game_swing_cone'] = entry['swing_cone']
    scene.frame_set(1)

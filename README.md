# Pepe Athletics · v0.3.0

A JavaScript pole-vault prototype with a detailed, rigged frog, a flexible pole, manual technique controls, and physical ragdoll flight and landings. Three.js renders the exported Blender assets; cannon-es handles released bodies, impacts, the crossbar and landing pad.

First tagged release. See [CHANGELOG.md](CHANGELOG.md) for release notes.

## Run

```sh
npm install
npm run dev -- --host 127.0.0.1 --port 5189
```

Open http://127.0.0.1:5189. The model loads before **Let’s vault** becomes available. `npm run build` creates `dist/`; `npm run preview -- --port 5189` serves it.

## Controls

| Key | Action |
| --- | --- |
| D / L | Tap alternately to move the left/right foot and build approach speed. Holding does not repeat a step. |
| H | Tap for an immediate quarter-step adjustment; hold about 0.33 s to lower the pole fully toward the plant. Releasing preserves that position. |
| Space | Plant anywhere; keep holding to store more launch energy (2-second cap). Releasing Space stops charging but keeps the grip. |
| J | Press at the green surge cue for a momentum boost; hold to swing the feet above the head. One boost per attempt. |
| K | Tap at the green throw cue after swinging up. Commits extension and automatically lets go. |
| P / Escape | Pause/resume the game and audio. |
| R | Reset to the start screen. |

Pepe starts at −32 m, with roughly 28 m to the classic planting zone. Faster alternating steps build speed. Planting preserves movement around the tip: waiting on the pole loses energy rather than freezing the body. A well-timed J impulse boosts that movement, K turns it into a throw, and holding Space longer adds height. Strong technique and a long charge can overshoot the mat, hit the distant wall, or leave the arena. The camera follows the flight.

**Body weight** is adjustable between attempts, from 50–180 kg (default 95 kg). The selected weight is distributed across all 15 physical bodies. Heavier Pepe accelerates more slowly, loads the pole differently, and receives less velocity from the same swing and spring energy; lighter Pepe accelerates and launches more easily. Gravity remains 9.81 m/s². Weight persists across retries and resets during the current page session.

**Watch demo** uses the same input handlers as the player, lighting D/L taps, H/J holds, Space charging, and the K throw. It demonstrates a short charge and early plant. P pauses simulation, charge, demo and sound together; any gameplay key or Take control hands the attempt to you. Touch buttons provide the same actions. The HUD separates stored power from the J/K timing window. A clean clearance requires passing above the bar, keeping it in place, and reaching the pad. Personal best is saved locally; demos do not award it.

## Motion and physics

The approach and limb movements use the reviewed Blender poses. D/L independently drive leg strides and H controls lowering. Once planted, a continuous angular simulation moves the whole pose around the fixed pole tip, with incoming run speed, spring acceleration, gravity, drag, body mass and one timed J impulse. Space stores additional spring energy, capped at two seconds. K completes the extension before releasing. Waiting too long loses the swing and causes a ragdoll fall.

This remains a hybrid controller: the angular motion responds to physics and inputs, while the limbs and pole bend follow the authored poses. It is not yet a fully force-driven muscle and elastic-pole simulation. On release or failure, 15 bodies become dynamic with 14 physical joints. Measured pose velocity is carried into the launch, with exaggerated spring and timing boosts. Gravity, rotation, contacts and crossbar collisions then determine the flight and landing. The skin follows the physical bodies; the pole stays at the planted location.

The supported crossbar drops on character contact. Simulation runs at 120 Hz. Crowd applause starts with the countdown. Failure triggers a gasp followed by boos; a clean landing triggers cheers, claps and whistles. There is no continuous crowd loop or music. P suspends audio and cancels speech. Mute and reset stop sounds. See `public/assets/audio/README.md`.

`src/rigged-vault.js` owns the model, body masses and pose-to-ragdoll handoff. `src/pole-momentum.js` owns the continuous planted arc, timing windows and Space charge. `src/vault-phases.js` controls limb phases, and `src/vault-power.js` converts incoming velocity, charge, mass and timing into launch velocity. `src/physics.js` preserves the earlier procedural prototype and is not the current controller.

## Assets and editing

- `blender/pepe-plant-rig.blend`: editable 217-frame rig, shoulder deformation helpers, flexible pole and marked phases.
- `public/assets/pepe-plant-animated.glb`: the model and pole currently loaded by the game.
- `public/assets/pepe-carry-ready.glb`, `pepe-plant-ready.glb`, `pepe-takeoff-ready.glb`, `pepe-inverted-ready.glb`: independent posed mesh exports.
- `public/assets/pepe-joint-limits.json` and `src/joint-limits.js`: calibrated bind-relative bone limits for future active joint control. The game’s ragdoll currently uses its own Cannon cone-twist bounds.
- `output/plant-rig/index.html`: orbitable motion study, frame scrubber and asset downloads.
- `output/plant-rig/versions/v1/`: local-only backup of the prior rig, clip, scripts and review images (excluded from Git).

The Tripo original, retopology and hand-grip source assets are unchanged. The current rig skins the source mesh directly, avoiding a second deformation of a previously baked carry pose. See `output/plant-rig/README.md` for the Blender pipeline.

## Checks

```sh
npm run check
npm run build
```

`blender/audit_plant_rig.py` checks the evaluated mesh, grip contact, tip anchor and joint continuity. Browser checks exercise the actual start/countdown, D/L approach, H raise, Space plant, timed J/K, Space charge, adjustable weight, P/audio pause, physical release, failure and reset. Local captures live in `output/playwright/`; the release validation summary is in `docs/validation-v0.3.0.md`.

Known visual limitation: the pole still intersects the torso during part of the rockback transition (frames 169–183). See `output/plant-rig/geometry-status.md`; the complete shaft/mesh audit is not yet passing.

Javelin and shot put remain future events. This local prototype has no account, backend, multiplayer or analytics.

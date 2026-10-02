# Changelog

## 0.3.0 — 2026-10-02

First tagged release of the playable pole-vault prototype.

### Added

- Adjustable body weight from 50 to 180 kg, defaulting to 95 kg. Weight changes the actual ragdoll mass, running acceleration, pole response and launch power.
- Continuous forward motion around the planted pole, preserving the approach momentum.
- A timed J swing boost and K throw, with visible timing cues.
- Hold Space after planting to charge a stronger, higher launch, with a two-second power cap and live meter.
- A keyboard demonstration that lights up taps and holds using the same controls as the player.
- A long runway, planting anywhere before the bar, exaggerated launches, stadium-wall collisions and out-of-arena results.

### Included from earlier development

- A detailed frog and flexible pole exported from Blender, with editable source models and rig.
- D/L alternating foot controls and fast H pole lowering.
- A 15-body physical ragdoll with 14 joints after release or failure, plus a falling crossbar and adjustable bar height.
- Countdown beeps, opening applause, shocked/booing crowd reactions on failure, and cheers/claps/whistles on a clean landing.
- Pause for gameplay and audio, touch controls, responsive layout, and local personal bests.

### Changed

- K now commits the throw and releases automatically. A second Space press is no longer needed.
- Waiting on the pole loses momentum and eventually causes a fall instead of freezing the body.
- Removed continuous humming/background ambience.

### Validation and limitations

- Automated checks cover phase controls, pole momentum, timing, charge, mass-dependent power, demo input, joint bounds and audio lifecycle.
- Browser checks exercise the imported model and actual game controls.
- The planted arc responds to physics; limb movement and pole bending still use reviewed Blender poses. Full ragdoll physics takes over on release or failure.
- Known visual issue: the pole intersects the torso during part of rockback (frames 169–183).
- Javelin and shot put are future events.

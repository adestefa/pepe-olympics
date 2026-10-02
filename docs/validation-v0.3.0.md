# v0.3.0 validation — 2026-10-02

The game was exercised in an isolated Chromium browser using the real UI and shared keyboard handlers. The model and collision bodies were loaded from the production GLB. Measurements are approximate, with input edges sampled on browser frames.

## Gameplay comparisons

All comparison attempts used alternating D/L taps every 0.26 seconds, fully lowered the pole with H, and planted near x = −12 m. Good J and K timing scored approximately 0.96–0.99 on a 0–1 scale. “Held Space” means continuously from plant until release; release occurred before the two-second charge cap.

| Weight | Space | J timing | Speed after six steps | Launch x/y velocity | Peak hip height | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 95 kg | 0.13 s | Good | 4.70 m/s | 20.31 / 11.20 m/s | 9.62 m | Stadium wall crash |
| 95 kg | Held | Good | 4.70 m/s | 22.34 / 19.65 m/s | 20.55 m | Left the stadium |
| 50 kg | Held | Good | 9.36 m/s | 46.68 / 29.99 m/s | 28.76 m | Left the stadium |
| 180 kg | Held | Good | 2.31 m/s | 9.72 / 13.49 m/s | 12.79 m | Overshot the mat |
| 95 kg | 0.13 s | 0.4 s late | 4.68 m/s | 11.26 / 7.29 m/s | 6.75 m | Overshot the mat |

- Physical body mass summed to the selected 50, 95 or 180 kg.
- At 95 kg, the body advanced another 0.31 m during 0.17 seconds at the loaded pose with no J input, confirming that the planted motion no longer freezes.
- The planted tip remained fixed within 0.00003 m in the demo samples.
- Every tested throw switched to 15 dynamic bodies and 14 joints.
- The default 95 kg demo cleared 4.2 m and landed on the pad, with all six input tiles lighting in sequence.
- P froze simulation time and Space charge, suspended audio, then resumed the demo to a clean landing.
- Body weight was locked during the attempt and unlocked on the result screen; the footer displayed v0.3.0.
- No browser JavaScript errors were captured during these attempts.

## Automated checks

`npm run check` covers 15 tests: joint bounds, audio lifecycle, phase progression, H input, continuous pole movement, one-shot J boosting, K timing, Space charging, weight-dependent response, launch power and demo input. `npm run build` produces the production bundle. Vite reports its existing large-bundle advisory for Three.js/Cannon.

## Existing limitation

The release retains the documented pole/torso intersection during rockback, frames 169–183. The full geometry audit is not passing; this release does not claim to fix that asset issue. See `output/plant-rig/geometry-status.md`.

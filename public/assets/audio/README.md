# Game audio

The crowd is event-driven. There is no looping ambience or background music.

| File | Cue | Length | Generation task |
| --- | --- | --- | --- |
| crowd-start.mp3 | Encouraging stadium applause at the countdown | 5 s | 66b87d86-f1e5-4246-8b10-316f843544be |
| crowd-failure.mp3 | Collective shocked gasp, pause, then disappointed boos | 6 s | 7ceac0f7-a2ef-4e6f-934f-92d74941b5a7 |
| crowd-success.mp3 | Cheers, hand clapping and human whistles | 7 s | 46e69478-9298-48e2-934f-218ed088a7fc |

These three stereo 44.1 kHz MP3s were generated for this project through the connected Runway sound-effects service on 2026-10-02. They are generated stadium effects, not recordings of the Olympic Games. Requests specified natural outdoor human crowds, no music, no announcer and no synthetic hum.

The failure gasp and boos are one continuous clip, so pausing the Web Audio context also pauses the transition between them. Each outcome plays once per round. Mute stops all active sources; unmute does not start background playback. Reset/retry stops the preceding round's sounds.

The legacy crowd-ambience.wav, crowd-cheer.wav and crowd-boo.wav are retained source assets but are not loaded or played. blender/build_audio.py regenerates only short countdown, impact and pole effects. Character dialogue WAVs are separate existing assets.

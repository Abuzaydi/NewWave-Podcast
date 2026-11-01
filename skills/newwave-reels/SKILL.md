---
name: newwave-reels
description: Edit New Wave podcast clips into Elisa-approved reels (horizontal + vertical): word-synced clean captions, real B-roll, punch-ins, original music and SFX.
---

# New Wave Reels

This is the editing style Elisa (New Wave host and editorial director) approved on 1 Nov 2026 for clip 02 of the Maurits Neo episode, "500K to zero at 15". Use it for every New Wave clip unless Ahmad or Elisa ask for something different. Ahmad usually works from his phone, so keep replies short and practical, and never ask him to run commands.

## Toolkit (scripts that produce the approved look)

The scripts are in `toolkit/` next to this file. A backup copy lives on a private Claude artifact (https://claude.ai/artifact/N8GYgnsdREXaWpNokQq3Xa, files under `files/`). Read `toolkit/README.txt` and `toolkit/example_spec_clip02.json` first: the example spec is the reference for every setting.

| File | What it does |
|---|---|
| make_clip.py | Cuts the clip from the HD episode, detects shots and faces, times every word, burns captions, adds B-roll, punch-ins and the black-and-white hit. Add `vertical` for 9:16. |
| timing.py | Reads the Descript SRT (episode.srt) and spreads words across each line as a first estimate. |
| wtime.py, wtime2.py | Exact word times with Whisper, matched back onto the transcript words. |
| shots.py | Shot cuts and face positions for caption placement and the vertical crop. |
| plan_audio.py | Builds the music and sound-effect plan from the clip's real word times. |
| score2.py | Generates the original music bed and effects. |
| mix.sh | Mixes voice, music and effects, ducks music under the voice, normalises to -14 LUFS. |
| gfx_counter.py | Animated "$500,000 to $0" portfolio counter, both formats. |
| gfx_label.py | Name label graphic (not used in the approved look). |
| grad_top.png, grad_bottom.png | Shade overlays for captions on bright B-roll. |

Workspace setup (once per session):
1. Fonts into ~/.fonts from github.com/google/fonts (ofl/poppins: Poppins-Bold, -ExtraBold, -SemiBold, -Medium; ofl/playfairdisplay: PlayfairDisplay-Italic[wght].ttf), then `fc-cache -f`.
2. Face detection: haarcascade_frontalface_default.xml and haarcascade_profileface.xml from github.com/opencv/opencv (4.x, data/haarcascades) into `./cascades`.
3. Whisper: `pip install faster-whisper`. The model downloads from Hugging Face (huggingface.co, *.huggingface.co, *.hf.co must be reachable).
4. `mkdir build out audio broll gfx` and put grad_*.png in `broll/`.

## Source footage

- Use the full HD episode (1920x1080). Episodes are in Google Drive, folder "New Wave Podcast Raw Videos". Direct download: `https://drive.usercontent.google.com/download?id=FILE_ID&export=download&confirm=t` (file shared as "Anyone with the link"). Do not export from Descript's free plan: it adds a watermark.
- Transcript: import the episode into Descript, export the transcript as SRT (save as episode.srt) and as TXT with speaker labels. The TXT tells you who speaks when.
- B-roll Ahmad records arrives on his Mac (Desktop or Downloads, via screen recording or AirDrop) or as chat attachments. macOS screen-recording names contain a narrow no-break space before AM/PM, so match them with a wildcard.

## Picking clips

About 40 s, never over 60 s. One standalone moment that makes sense without the episode: a strong opinion, a money or loss story, a surprising number, useful advice. Open on the hook, end on a complete thought. Give Ahmad start/end time, first and last words, a title and why it works, before rendering.

## Writing the spec

Copy example_spec_clip02.json and change: name, src, src_start/ep_start (episode seconds), dur, phrases, broll, punch, audio, and the override lists.
- phrases: one entry per spoken phrase, every word in spoken order (fillers like um/uh can be left out). Wrap 1-2 key words per phrase in *stars* (bold). Mark at most two hero words per clip with # inside the stars (`*#500K*`), shown big and red. Start a phrase with `!` to drop the picture to black and white on its hero word (use once, on the final punchline).
- Spell names and terms correctly in phrases even when the transcript is wrong (perps not PAPS, Maurits, ZEC).
- `cap_style: "clean"`, `cap_preset: "approved"` (the italic serif + bold sans look Elisa approved). `cap_preset: "straight"` is the upright, bigger, bolder alternative; use it only if asked.

## Caption rules (approved look)

One line at a time, grouped into natural phrases (never a lone word unless it is a hero word), words revealed exactly as spoken. Regular words in bold italic serif, key words in bold sans, white, thin soft drop shadow, no dark box or glow behind. Captions sit lower than the speaker's face: horizontal close-ups lower right, wide shots centred over the middle of the frame, vertical just under the chin above any shirt print. No name labels or lower-thirds. No full stops at the end of captions; question marks stay.

## B-roll rules

- 4-5 B-roll moments per clip, each with a clear meaning. No generic charts or trading screens: Elisa rejected "random charts".
- Prefer real footage of the guest from his own vlogs, Instagram or YouTube (it must clearly be him), real news headlines for events, and animated graphics for numbers.
- Every B-roll is full screen in both formats. Photos pan across the subject (`pan`/`vpan`). Headlines go dark mode (negate + hue 180, bottom shade) with captions underneath (`cap`/`capv` overrides, `vmode: fit` in vertical).
- Money drops use the animated counter (gfx_counter.py: $X counting to $0 with a red falling line), timed so $0 lands on the spoken word (`offset` about -1.15 s).
- Know the crypto meaning: "bear market" means the market going down, "bull run" means up. Never show a literal bear or bull.
- AI images only where no real footage exists (Higgsfield `z_image`, about 0.15 credits each on the free plan). AI video costs about 28 credits per shot, so ask first.
- Crop away YouTube or Instagram UI, usernames and on-screen titles from screen recordings.

## Sound

Original score only (score2.py), so nothing is copyright-flagged. Music bed at -24 dB under the voice with sidechain ducking. Swooshes, risers and hi-hats stay very quiet: loud ones read as a distracting "shh" noise. Keep the meaningful hits: cash sound on money gains, impacts on losses, glitch on scam words, ticks during the counter, music cut on the final punchline. Final loudness -14 LUFS (mix.sh). Always build the plan from real word times with plan_audio.py, never hand-typed times.

## Render order

```
python3 make_clip.py spec.json            # horizontal 1920x1080
python3 make_clip.py spec.json vertical   # vertical 1080x1920
python3 plan_audio.py NAME spec.json audio/p.json
python3 score2.py audio/p.json audio/s.wav
./mix.sh build/NAME_nomusic.mp4 audio/s_music.wav audio/s_sfx.wav out/NAME_v1.mp4
```

Name every delivery with a version number (CLIPNAME_v1.mp4, CLIPNAME_v1_vertical.mp4, v2...) so old downloads never get confused with new ones.

## Checks before sending (do all)

1. Picture sync: compare frames of the output against the cut source at 6-8 times; the best match must be at offset 0. The HD episode is 29.97 fps, so the video chain must start with `fps=25` before zoompan (already in make_clip.py); without it the picture drifts behind the voice.
2. Word sync: the build prints "verbatim-aligned"; spot-check that caption appearance times equal the Whisper word times, including repeated words ("how is, like, how is it").
3. Speaker on screen: in vertical, make sure the crop shows whoever is talking. When the source cuts to a two-shot of the hosts, set `vcx_override` to the speaker's position.
4. Frame grid of both formats at key moments: captions readable, not on faces or busy shirt prints, nothing off the edge.
5. Decode check and loudness about -14 LUFS.

## Feedback loop

Elisa's process: reference video, then skill, then feedback until perfect, then refine this skill. Put Ahmad's and Elisa's notes into the spec, re-render, send the new version. If Ahmad says something is out of sync, ask for a phone screen recording with sound of the exact version, then measure it (Whisper on the recording plus frame comparison) before changing anything. When a note becomes a standing rule, update this file.

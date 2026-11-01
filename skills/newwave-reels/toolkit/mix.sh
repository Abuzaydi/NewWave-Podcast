#!/bin/bash
# mix.sh VIDEO_NOMUSIC MUSIC SFX OUT
ffmpeg -v error -y -i "$1" -i "$2" -i "$3" -filter_complex "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asplit=2[d][sc];[1:a]volume=-24dB[m];[m][sc]sidechaincompress=threshold=0.04:ratio=3:attack=20:release=350[md];[2:a]volume=-6dB[fx];[d][md][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart "$4"

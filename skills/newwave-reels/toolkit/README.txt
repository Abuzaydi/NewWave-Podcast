New Wave Reels toolkit (approved by Elisa, Nov 2026 — clip 02 "500K to zero", v9 look)
Setup in a fresh workspace:
  mkdir -p ~/.fonts && fetch Poppins (Bold, ExtraBold, SemiBold, Medium) + PlayfairDisplay-Italic[wght] from github.com/google/fonts (ofl/poppins, ofl/playfairdisplay); fc-cache -f
  mkdir cascades && fetch haarcascade_frontalface_default.xml + haarcascade_profileface.xml from github.com/opencv/opencv/4.x/data/haarcascades
  NO_PROXY= no_proxy= pip install --break-system-packages faster-whisper   (needs huggingface.co, *.huggingface.co, *.hf.co allowed)
  put episode.srt (Descript SRT export of the full episode) next to the scripts; mkdir build out audio broll gfx; move grad_*.png into broll/
Run:  python3 make_clip.py spec.json            (horizontal 1920x1080)
      python3 make_clip.py spec.json vertical   (vertical 1080x1920)
      python3 plan_audio.py <name> spec.json audio/p.json ; python3 score2.py audio/p.json audio/s.wav
      ./mix.sh build/<name>_nomusic.mp4 audio/s_music.wav audio/s_sfx.wav out/<name>.mp4

# Integration test checklist

## pinky.local (TrueNAS API)

- [ ] `curl http://pinky.local:8787/health` returns `"status":"ok"`
- [ ] `curl http://pinky.local:8787/api/v1/slideshow` returns 5 slides in order
- [ ] `/media/radar_reflectivity.jpg` returns JPEG (1024×600)
- [ ] After 3+ minutes, `last_refresh` updates (scheduler running)
- [ ] Disconnect WAN briefly; cached media still serves

## brain.local (ESP32-P4)

- [ ] Device resolves `pinky.local` and joins WiFi as hostname `brain`
- [ ] Slideshow auto-advances every 10 s
- [ ] Single tap toggles pause; indicator fades
- [ ] While paused: swipe left/right changes slide
- [ ] Weather slide shows live JSON fields
- [ ] Radar/outlook JPEGs load without reboot
- [ ] Pinch zoom works on image slides; resets on slide change
- [ ] New SVR/TOR alert plays one WAV; no repeat on unchanged poll

## End-to-end

- [ ] Power-cycle brain; resumes slideshow within one poll cycle
- [ ] Update GHCR image on pinky; restart app; brain picks up new revisions via `?r=` tokens

# TrueNAS Custom App — pinky.local

Deploy the slideshow API on TrueNAS SCALE using **Apps → Discover Apps → Custom App → ⋮ → Install via YAML**.

## Dataset (your setup)

Create a **child dataset** under the existing **apps** dataset (the one TrueNAS uses for application storage):

**`apps` → `esp32-weather-slideshow`**

**pinky.local:** pool name is **`apps`**. Docker bind mount:

```yaml
- /mnt/apps/esp32-weather-slideshow:/data
```

## Prerequisites

- TrueNAS SCALE 24.10+ with Apps enabled
- Dataset **`apps/esp32-weather-slideshow`** created
- GHCR image public **or** registry credentials for private pulls
- mDNS/DNS: clients resolve `pinky.local` on the LAN

## Install

1. Paste [deploy/truenas/compose.yaml](../deploy/truenas/compose.yaml) into **Custom Config** (⋮ → Install via YAML).
2. Port **8787** → **8080** is already in the file.
3. Verify:

   ```bash
   curl -s http://pinky.local:8787/health
   # Expect: "spc_basemap_bundled": true and spc_revision not stuck on an old value
   curl -s http://pinky.local:8787/api/v1/slideshow | head
   ```

## Updating (without reinstalling)

TrueNAS often **reuses a cached `latest` image** on a simple restart. You do **not** need to delete and recreate the app every time.

1. Confirm GitHub Actions **Publish API image** finished for the commit you want.
2. **Apps → Installed Applications → esp32-weather-slideshow**
3. Use **Update** / **Upgrade** (wording varies by SCALE version). That redeploys and should pull a fresh image.
4. If the version did not change, **Edit** the app → open YAML → **Save** (no changes required). Compose includes `pull_policy: always` so Docker pulls `latest` again.
5. Check:

   ```bash
   curl -s http://pinky.local:8787/health
   ```

   Compare `api_version` and feature fields to what you expect from the repo.

**Optional — pin a build:** replace `image: ...:latest` with a GHCR tag from GitHub Packages (commit SHA), then Upgrade once. Useful when you want an exact known build.

**Last resort:** delete the app and reinstall from YAML (keeps data on `/mnt/apps/esp32-weather-slideshow` if the volume mount path is unchanged).

## Radar crop tuning

Shift the view on the host without rebuilding. The box is then widened to the panel's 16:10 shape so the image is not stretched. Reflectivity is the Iowa Environmental Mesonet N0Q mosaic, and velocity is Fort Worth base velocity (FWS N0U). Both are drawn over county outlines and names. If a fetch fails, that slide falls back to the NWS Ridge GIF.

| Variable | Example | Meaning |
|----------|---------|---------|
| `RADAR_BBOX` | `-97.08,32.78,-96.28,33.82` | west,south,east,north (degrees) |
| `RIDGE_OFFSET_KM_EAST` | `16.093` | ~10 miles east |
| `RIDGE_OFFSET_KM_NORTH` | `0` | north/south nudge (km) |

Edit YAML → Save → wait ~3 minutes for radar refresh.

## brain.local

```text
CONFIG_SLIDESHOW_BASE_URL="http://pinky.local:8787"
```

## Troubleshooting

- **Radar slides show `"revision":"0"`** — Ridge URLs must use `ridge/standard/`; velocity uses `base_velocity/KFWS_0.gif`.
- **SPC outlook has no state map** — Pull a recent API image; `spc_basemap_bundled` in `/health` should be `true`.
- **Permission denied on volume**: path must be `/mnt/apps/esp32-weather-slideshow`.
- **Avoid custom Docker networks** in Compose v1.
- **Outbound API failures**: cached media under `/data` until refresh succeeds.

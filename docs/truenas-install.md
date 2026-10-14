# TrueNAS Custom App — pinky.local

Deploy the slideshow API on TrueNAS SCALE using **Apps → Discover Apps → Custom App → ⋮ → Install via YAML**.

## Dataset (your setup)

Create a **child dataset** under the existing **apps** dataset (the one TrueNAS uses for application storage):

**`apps` → `esp32-weather-slideshow`**

That matches the usual Apps layout. You do not need a separate top-level path like `tank/apps/...` unless your pool is literally named that way.

On the host, Docker needs the **absolute** bind path:

```text
/mnt/<pool-name>/apps/esp32-weather-slideshow
```

The dataset **Details** panel often shows only the ZFS-relative path:

```text
apps/esp32-weather-slideshow
```

That is normal — it is not the Docker mount path.

### Find `<pool-name>` (pick one)

1. **Storage → Pools** — the pool name is in the table (e.g. `tank`, `storage`, `main`).  
   Bind mount: `/mnt/THAT_NAME/apps/esp32-weather-slideshow`

2. **Datasets tree** — the **root** row above `apps` and `storage` is usually the pool name.

3. **Shell on pinky** (SSH):

   ```bash
   zfs list -H -o name,mountpoint | grep esp32-weather-slideshow
   ```

   Use the `mountpoint` column (starts with `/mnt/`).

**pinky.local:** the pool is named **`apps`** (Storage → Pools), not `tank`. Dataset ZFS path `apps/esp32-weather-slideshow` → Docker bind:

```yaml
- /mnt/apps/esp32-weather-slideshow:/data
```

Rule: `/mnt/` + **pool name** + `/` + **dataset path below the pool root**. Here the dataset is a direct child of pool `apps`, so there is only one `apps` in the mount path.

## Prerequisites

- TrueNAS SCALE 24.10+ with Apps enabled
- Dataset **`apps/esp32-weather-slideshow`** created (as above)
- GHCR image public **or** registry credentials configured in TrueNAS for private pulls
- mDNS/DNS: clients resolve `pinky.local` to this host

## Steps

1. **Dataset** — Already done if you see `esp32-weather-slideshow` under `apps`.

2. **Edit Compose mount** — In [deploy/truenas/compose.yaml](../deploy/truenas/compose.yaml), replace `/mnt/POOL/apps/esp32-weather-slideshow` with your real path from the dataset screen.

3. **Install via YAML** — Paste the edited Compose into **Custom Config**.

4. **Environment** — Optional overrides from [deploy/truenas/.env.example](../deploy/truenas/.env.example) (lat/lon, `NWS_USER_AGENT`, etc.).

5. **Port** — Host **8787** → container **8080** (already in Compose).

6. **Verify**

   ```bash
   curl -s http://pinky.local:8787/health
   curl -s http://pinky.local:8787/api/v1/slideshow | head
   ```

## brain.local

Configure the ESP32-P4 firmware with:

```text
CONFIG_SLIDESHOW_BASE_URL="http://pinky.local:8787"
```

Ensure the display can reach pinky on the LAN (same VLAN, no client isolation).

## Updates

Pull a new image tag from GHCR (`latest` or commit SHA), then restart the app from the TrueNAS UI.

## Troubleshooting

- **Radar slides show `"revision":"0"`** — Ridge GIF URLs must use lowercase `ridge/standard/` (not `Standard/`). Add `RIDGE_REFLECTIVITY_URL` / `RIDGE_VELOCITY_URL` to Compose (see [compose.yaml](../deploy/truenas/compose.yaml)), restart the app, wait ~3 minutes, then re-check `/api/v1/slideshow`. Or pull a newer GHCR image that includes the fix.
- **Permission denied on volume**: path must match the dataset mount exactly; Apps role on parent `apps` is normal.
- **Avoid custom Docker networks** in Compose v1; use default bridge + published ports only.
- **Outbound API failures**: cached JPEGs and last JSON remain under `/data` until refresh succeeds.

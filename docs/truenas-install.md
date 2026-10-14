# TrueNAS Custom App — pinky.local

Deploy the slideshow API on TrueNAS SCALE using **Apps → Discover Apps → Custom App → Install via YAML**.

## Prerequisites

- TrueNAS SCALE 24.10+ with Apps enabled
- Dataset: `/mnt/tank/apps/esp32-weather-slideshow` (adjust pool name if not `tank`)
- GHCR image public **or** registry credentials configured in TrueNAS for private pulls
- mDNS/DNS: clients resolve `pinky.local` to this host

## Steps

1. **Create dataset**  
   Storage → Datasets → Add dataset `tank/apps/esp32-weather-slideshow`.

2. **Copy environment**  
   Use [deploy/truenas/.env.example](../deploy/truenas/.env.example) values in the Custom App environment section, or bind an env file if your SCALE version supports it.

3. **Install via YAML**  
   Paste [deploy/truenas/compose.yaml](../deploy/truenas/compose.yaml) into **Custom Config**.

4. **Port**  
   Host **8787** → container **8080**.

5. **Verify**

   ```bash
   curl -s http://pinky.local:8787/health
   curl -s http://pinky.local:8787/api/v1/slideshow | head
   ```

## brain.local

Configure the ESP32-P4 firmware with:

```
CONFIG_SLIDESHOW_BASE_URL="http://pinky.local:8787"
```

Ensure the display can reach pinky on the LAN (same VLAN, no client isolation).

## Updates

Pull a new image tag from GHCR (`latest` or commit SHA), then restart the app from the TrueNAS UI.

## Troubleshooting

- **Permission denied on volume**: confirm the dataset path exists and Apps storage is configured.
- **Avoid custom Docker networks** in Compose v1; use default bridge + published ports only.
- **Outbound API failures**: cached JPEGs and last JSON remain under `/data` until refresh succeeds.

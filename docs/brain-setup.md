# brain.local — ESP32-P4 firmware

Slideshow client for the Elecrow CrowPanel Advanced 10.1" (ESP32-P4 + C6 WiFi).

## Hardware (10.1" Advanced)

| Item | Spec |
|------|------|
| SoC | ESP32-P4 dual-core RISC-V (400 MHz HP + LP core) — **silicon rev v1.x** on current boards |
| Memory | **16 MB** flash, **32 MB** PSRAM (HEX / 16-line mode in IDF) |
| Display | 10.1" IPS **1024×600**, capacitive touch (GT911) |
| Wireless | **ESP32-C6-MINI-1** module (Wi‑Fi 6 / BLE 5.3) — not the P4’s built-in radio |
| Debug / flash | **UART0** USB-C (CH340); optional second USB-C for power / USB 2.0 device |

`sdkconfig.defaults` in `firmware/` matches Elecrow’s ESP-IDF examples (rev &lt;3.0, 16 MB flash, PSRAM). After changing defaults, delete `firmware/sdkconfig` and rebuild.

## Prerequisites

- [ESP-IDF 5.4+](https://docs.espressif.com/projects/esp-idf/) with **esp32p4** support (IDF **6.x** uses managed [`espressif/cjson`](https://components.espressif.com/components/espressif/cjson) instead of the old built-in `json` component)
- Elecrow ESP-IDF examples for MIPI-DSI display + GT911 touch
- pinky slideshow API at `http://pinky.local:8787` (see [truenas-install.md](truenas-install.md))

## Activate ESP-IDF (each new terminal)

Install path on this machine: `C:\esp32\v6.1\esp-idf`

### One-time: install tools + Python venv

If `export.bat` says the Python env under `%USERPROFILE%\.espressif\python_env\...` is missing, run **once** in CMD:

```bat
cd C:\esp32\v6.1\esp-idf
install.bat esp32p4
```

(Waits 10–30+ minutes; downloads compiler, OpenOCD, and creates `idf6.1_py3.13_env`.)

Then continue with `export.bat` below.

**Important:** Running `export.bat` **from PowerShell** does **not** put `idf.py` on your PATH (the batch file only updates **cmd.exe**). Use **CMD** or **`export.ps1`** below — not `export.bat` inside PowerShell.

**CMD (recommended):**

Open **Command Prompt** (Win+R → `cmd`), then:

```bat
C:\esp32\v6.1\esp-idf\export.bat
idf.py --version
```

Or one shot from PowerShell — opens a CMD window with IDF active:

```powershell
cmd.exe /k "C:\esp32\v6.1\esp-idf\export.bat"
```

**PowerShell** — use **`export.ps1`** (not `export.bat`). If scripts are blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& C:\esp32\v6.1\esp-idf\export.ps1
idf.py --version
```

(`-Scope Process` only affects this window; does not change system policy.)

Or one line:

```powershell
powershell -ExecutionPolicy Bypass -NoExit -File C:\esp32\v6.1\esp-idf\export.ps1
```

**Git Bash (Cursor):**

```bash
. /c/esp32/v6.1/esp-idf/export.sh
idf.py --version
```

## Configure

```bash
cd firmware
idf.py set-target esp32p4
idf.py menuconfig
```

**Slideshow**

- `SLIDESHOW_BASE_URL` → `http://pinky.local:8787`
- WiFi SSID / password
- Poll and advance intervals (defaults match pinky)

**PSRAM / flash** — should come from `sdkconfig.defaults` (16 MB + SPIRAM). Confirm in menuconfig if flash still shows 2 MB.

**WiFi on C6** — the P4 has **no** on-die WiFi. Managed components **`espressif/esp_hosted`** + **`espressif/esp_wifi_remote`** route normal `esp_wifi_*` calls to the C6 over SDIO (`sdkconfig.defaults.esp32p4`). The C6 ships with ESP-Hosted **slave** firmware; if you see `esp_wifi_remote_weak … unsupported`, rebuild after pulling deps and delete `sdkconfig`.

**SDIO + host stack (10.1" / V1.2)** — Match Elecrow’s [V1.2 Lesson16 WiFi example](https://github.com/Elecrow-RD/CrowPanel-Advanced-7inch-ESP32-P4-HMI-AI-Display-1024x600-IPS-Touch-Screen/tree/master/example/V1.2/idf-code/Lesson16_Get_weather_via_WiFi) for **SDIO pins, LDO3, and factory C6** (no C6 reflash required in most cases). Elecrow’s demo uses **IDF 5.5.4** with **`esp_hosted` 2.7.0** + **`esp_wifi_remote` 0.16.1**. This repo on **IDF 6.1** uses **`esp_wifi_remote` ~1.6.5** + **`esp_hosted` ~2.12** (same pairing as ESP-IDF’s P4 Wi-Fi examples): newer **injected Wi-Fi headers** and host RPCs required to compile against IDF 6.1. **LDO3 @ 2.5 V** in `crowpanel_board_init`, SDIO **CMD 19 / CLK 18 / D0–D3 17→14** (not 14→17), C6 reset **GPIO 54** — **`sdkconfig.defaults.esp32p4.elecrow_v12`**. Older **V1.0** boards: pins **52–49**, reset **20** (`sdkconfig.defaults.esp32p4` only, no `elecrow_v12` overlay). If the slave never comes up on IDF 6.1, try Elecrow’s optional C6 upgrade or build with **IDF 5.5.4** and Elecrow’s exact component versions.

```powershell
Remove-Item -Force sdkconfig
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.esp32p4;sdkconfig.defaults.esp32p4.elecrow_v12" set-target esp32p4
idf.py build flash monitor
```

Re-enter WiFi SSID/password after deleting `sdkconfig`.

## If WiFi still fails after V1.2 host config

`Not able to connect with ESP-Hosted slave` with **wrong** D0–D3 order often looks like a bad C6 — fix **V1.2 pins** and **LDO3** first. On **IDF 6.1**, ensure **`esp_hosted` ~2.12** pulled in (delete `managed_components` + `dependencies.lock` after `git pull`). If it persists, Elecrow’s optional [C6 upgrade guide](https://github.com/Elecrow-RD/CrowPanel-Advanced-7inch-ESP32-P4-HMI-AI-Display-1024x600-IPS-Touch-Screen/tree/master/example/V1.2/Upgrade%20P4%20to%20C6%20firmware) or matching **IDF 5.5.4 + esp_hosted 2.7.0** host stack.

## Integrate Elecrow BSP

Display/touch come from Elecrow’s **`bsp_display`** / **`bsp_i2c`** components (Lesson16 V1.2), wired through [`crowpanel_board.c`](../firmware/components/crowpanel/crowpanel_board.c). After changing BSP-related `sdkconfig.defaults`, delete `sdkconfig` and rebuild.

## Build and flash

```bash
idf.py build flash monitor
```

On boot, **brain** should join WiFi, poll `/api/v1/slideshow`, auto-advance every 10 s, and load radar/outlook JPEGs from pinky.

## Interaction (pre-plan)

- Tap: pause / resume
- Swipe left/right while paused: change slide
- Pinch on image slides: zoom (basic)

## Troubleshooting

| Issue | Check |
|-------|--------|
| CMake: missing `idf_v6.1/esp_wifi_remote_weak.c` | **`esp_wifi_remote` 0.16.1** has no IDF 6.1 tree — use **~1.6.5** + **`esp_hosted` ~2.12**; delete `managed_components`, `dependencies.lock`, `sdkconfig`, then `set-target esp32p4` |
| Compile: `ESP_WIFI_NAN_NDP_PMK_LEN` / `nan_vendor_ie_t` undeclared in `esp_private/wifi.h` | Stale **`esp_wifi_remote` 1.3.x** injected headers vs IDF 6.1 — bump to **~1.6.5** (and **esp_hosted ~2.12**); clean `managed_components` and rebuild |
| CMake: `json` / `lvgl` not found | IDF 6 — use managed deps in `main/idf_component.yml` (`espressif/cjson`, `lvgl/lvgl`); `git pull` then `idf.py reconfigure` |
| Flash: bootloader needs **v3.1–v3.99**, chip is **v1.3** | Do **not** use `--force`. Rebuild for v1.x: `sdkconfig.defaults` sets `ESP32P4_SELECTS_REV_LESS_V3`; delete local `firmware/sdkconfig`, then `idf.py fullclean` → `set-target esp32p4` → `build` → `flash` |
| `esp_wifi_remote_weak` / `ESP_ERR_NOT_SUPPORTED` at `esp_wifi_init` | Add `esp_hosted` + `esp_wifi_remote` (in `main/idf_component.yml`); delete `sdkconfig`, `idf.py reconfigure` so `sdkconfig.defaults.esp32p4` applies |
| `sdio_mempool_create` / `HS_MP: mempool create failed` | Enable `CONFIG_ESP_HOSTED_MEMPOOL_PREFER_SPIRAM` + `CONFIG_FREERTOS_HZ=1000` (in defaults); use `esp_hosted` ≥ 2.12.8; rebuild after deleting `sdkconfig` |
| No data | `ping pinky.local` from LAN; URL in menuconfig |
| JPEG slides blank | PSRAM enabled; serial log `image_loader` / `esp_jpeg` |
| WiFi fails | SSID/password; 2.4 GHz |
| `Not able to connect with ESP-Hosted slave` | V1.2 overlay: **D0=17…D3=14**, reset **54**, **LDO3**; IDF 6.1: **esp_hosted ~2.12**; delete `sdkconfig` + `managed_components` and rebuild |
| Old slides after pinky update | Normal; brain polls every ~45 s |

## Integration checklist

See [integration-test.md](integration-test.md) — **brain.local** section.

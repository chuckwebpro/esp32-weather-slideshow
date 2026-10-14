#pragma once

#include "net/slideshow_client.h"
#include "esp_err.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t alert_audio_init(void);

/** Play WAV for new/updated SVR/TOR alerts; dedupe via NVS. */
void alert_audio_handle_manifest(const slideshow_manifest_t *manifest);

#ifdef __cplusplus
}
#endif

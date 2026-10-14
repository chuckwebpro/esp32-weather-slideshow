#pragma once

#include "esp_err.h"
#include "lvgl.h"
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Decode JPEG bytes and assign to LVGL image widget (RGB565 in PSRAM when available). */
esp_err_t slideshow_image_set_jpeg(lv_obj_t *img, const uint8_t *jpeg, size_t jpeg_len);

/** Release decode buffers (call on shutdown if needed). */
void slideshow_image_loader_deinit(void);

#ifdef __cplusplus
}
#endif

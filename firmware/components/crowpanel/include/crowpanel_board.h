#pragma once

#include "esp_err.h"
#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Initialize MIPI-DSI panel and GT911 touch (Elecrow BSP). */
esp_err_t crowpanel_board_init(void);

/** Lock LVGL port mutex before UI calls (no-op if port not used). */
void crowpanel_lvgl_lock(void);

void crowpanel_lvgl_unlock(void);

#ifdef __cplusplus
}
#endif

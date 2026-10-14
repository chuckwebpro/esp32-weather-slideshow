#include "crowpanel_board.h"

#include "esp_log.h"

static const char *TAG = "crowpanel";

esp_err_t crowpanel_board_init(void)
{
    /* TODO: Wire Elecrow ESP-IDF example — MIPI-DSI 1024x600 + GT911 + LVGL port. */
    ESP_LOGW(TAG, "Using stub board init; integrate Elecrow display/touch drivers");
    return ESP_OK;
}

void crowpanel_lvgl_lock(void) {}

void crowpanel_lvgl_unlock(void) {}

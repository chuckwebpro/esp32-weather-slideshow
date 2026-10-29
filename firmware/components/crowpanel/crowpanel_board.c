#include "crowpanel_board.h"

#include "bsp_display.h"
#include "bsp_i2c.h"
#include "esp_ldo_regulator.h"
#include "esp_log.h"
#include "esp_lvgl_port.h"

static const char *TAG = "crowpanel";

static esp_ldo_channel_handle_t s_ldo3;

esp_err_t crowpanel_board_init(void)
{
    /* Elecrow Lesson16: LDO3 @ 2.5 V — IO domain + MIPI DPHY (VDD_MIPI_DPHY). */
    const esp_ldo_channel_config_t ldo3 = {
        .chan_id = 3,
        .voltage_mv = 2500,
    };
    esp_err_t err = esp_ldo_acquire_channel(&ldo3, &s_ldo3);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "LDO3 enable failed: %s", esp_err_to_name(err));
        return err;
    }

    err = i2c_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "I2C init failed: %s", esp_err_to_name(err));
        return err;
    }

    err = touch_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "touch init failed: %s", esp_err_to_name(err));
        return err;
    }

    err = display_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "display init failed: %s", esp_err_to_name(err));
        return err;
    }

    ESP_LOGI(TAG, "CrowPanel 1024x600 MIPI-DSI + GT911 ready");
    return ESP_OK;
}

void crowpanel_lvgl_lock(void)
{
    lvgl_port_lock(0);
}

void crowpanel_lvgl_unlock(void)
{
    lvgl_port_unlock();
}

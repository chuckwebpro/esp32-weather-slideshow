#include "sdkconfig.h"

#include "audio/alert_audio.h"
#include "crowpanel_board.h"
#include "net/slideshow_client.h"
#include "net/wifi_sta.h"
#include "ui/slideshow_ui.h"

#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

static const char *TAG = "app";

static slideshow_ui_t *s_ui;
static slideshow_manifest_t s_manifest;

static void advance_timer_cb(lv_timer_t *t)
{
    slideshow_ui_t *ui = lv_timer_get_user_data(t);
    if (slideshow_ui_is_paused(ui)) {
        return;
    }
    slideshow_ui_next(ui);
}

static void poll_task(void *arg)
{
    (void)arg;
    while (true) {
        if (slideshow_fetch_manifest(&s_manifest) == ESP_OK) {
            size_t keep = 0;
            crowpanel_lvgl_lock();
            if (s_ui) {
                keep = slideshow_ui_current_index(s_ui);
            }
            slideshow_ui_set_manifest(s_ui, &s_manifest);
            if (keep >= s_manifest.slide_count) {
                keep = 0;
            }
            slideshow_ui_show_slide(s_ui, keep);
            crowpanel_lvgl_unlock();
            alert_audio_handle_manifest(&s_manifest);
        }
        uint32_t wait = s_manifest.refresh_after_ms;
        if (wait < 10000) {
            wait = CONFIG_SLIDESHOW_POLL_MS;
        }
        vTaskDelay(pdMS_TO_TICKS(wait));
    }
}

void app_main(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    ESP_ERROR_CHECK(crowpanel_board_init());
    lv_init();

    ESP_ERROR_CHECK(wifi_sta_connect());

    ESP_ERROR_CHECK(slideshow_client_init(CONFIG_SLIDESHOW_BASE_URL));
    ESP_ERROR_CHECK(alert_audio_init());

    crowpanel_lvgl_lock();
    lv_obj_t *scr = lv_screen_active();
    s_ui = slideshow_ui_create(scr);
    lv_timer_create(advance_timer_cb, CONFIG_SLIDESHOW_ADVANCE_MS, s_ui);
    crowpanel_lvgl_unlock();

    xTaskCreate(poll_task, "slideshow_poll", 12288, NULL, 5, NULL);

    ESP_LOGI(TAG, "brain.local slideshow → %s", CONFIG_SLIDESHOW_BASE_URL);
    while (true) {
        vTaskDelay(pdMS_TO_TICKS(5));
        crowpanel_lvgl_lock();
        lv_timer_handler();
        crowpanel_lvgl_unlock();
    }
}

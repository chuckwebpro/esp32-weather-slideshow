#include "sdkconfig.h"

#include "audio/alert_audio.h"
#include "crowpanel_board.h"
#include "net/slideshow_client.h"
#include "ui/slideshow_ui.h"

#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

static const char *TAG = "app";

static slideshow_ui_t *s_ui;
static slideshow_manifest_t s_manifest;

static void wifi_init_sta(void)
{
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    /* Credentials via menuconfig Example Connection Configuration */
}

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
            crowpanel_lvgl_lock();
            slideshow_ui_set_manifest(s_ui, &s_manifest);
            slideshow_ui_show_slide(s_ui, 0);
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
    wifi_init_sta();

    ESP_ERROR_CHECK(slideshow_client_init(CONFIG_SLIDESHOW_BASE_URL));
    ESP_ERROR_CHECK(alert_audio_init());

    crowpanel_lvgl_lock();
    lv_obj_t *scr = lv_screen_active();
    s_ui = slideshow_ui_create(scr);
    lv_timer_create(advance_timer_cb, CONFIG_SLIDESHOW_ADVANCE_MS, s_ui);
    crowpanel_lvgl_unlock();

    xTaskCreate(poll_task, "slideshow_poll", 8192, NULL, 5, NULL);

    ESP_LOGI(TAG, "brain.local slideshow running → %s", CONFIG_SLIDESHOW_BASE_URL);
    while (true) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        crowpanel_lvgl_lock();
        lv_timer_handler();
        crowpanel_lvgl_unlock();
    }
}

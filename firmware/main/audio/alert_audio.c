#include "alert_audio.h"

#include "esp_log.h"
#include "nvs.h"
#include "nvs_flash.h"
#include <string.h>

static const char *TAG = "alert_audio";
static const char *NVS_NS = "alerts";

esp_err_t alert_audio_init(void)
{
    /* TODO: I2S pin map from Elecrow schematic; esp_codec_dev or raw I2S WAV parser. */
    ESP_LOGI(TAG, "alert audio init (I2S wiring pending Elecrow pins)");
    return ESP_OK;
}

static bool is_audio_event(const char *event)
{
    if (!event) {
        return false;
    }
    return strcmp(event, "Severe Thunderstorm Warning") == 0 ||
           strcmp(event, "Tornado Warning") == 0;
}

static bool nvs_seen_alert(const char *id, const char *updated)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READWRITE, &h) != ESP_OK) {
        return false;
    }
    char key[32];
    snprintf(key, sizeof(key), "a%.24s", id);
    char prev[40] = {0};
    size_t len = sizeof(prev);
    esp_err_t err = nvs_get_str(h, key, prev, &len);
    if (err == ESP_OK && strcmp(prev, updated) == 0) {
        nvs_close(h);
        return true;
    }
    nvs_set_str(h, key, updated);
    nvs_commit(h);
    nvs_close(h);
    return false;
}

static void play_stub(const char *event)
{
    ESP_LOGW(TAG, "PLAY WAV: %s (embed svr.wav / tor.wav)", event);
}

void alert_audio_handle_manifest(const slideshow_manifest_t *manifest)
{
    if (!manifest) {
        return;
    }
    for (size_t i = 0; i < manifest->alert_count; i++) {
        const alert_item_t *a = &manifest->alerts[i];
        if (!is_audio_event(a->event)) {
            continue;
        }
        if (nvs_seen_alert(a->id, a->updated)) {
            continue;
        }
        play_stub(a->event);
    }
}

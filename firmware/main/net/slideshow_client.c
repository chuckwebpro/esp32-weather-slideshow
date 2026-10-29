#include "slideshow_client.h"

#include "esp_http_client.h"
#include "esp_log.h"
#include "cJSON.h"
#include <stdlib.h>
#include <string.h>

static const char *TAG = "slideshow_client";
static char s_base_url[128];

static esp_err_t http_get_to_buffer(const char *url, char **out_body, int *out_len)
{
    esp_http_client_config_t cfg = {
        .url = url,
        .timeout_ms = 15000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    if (!client) {
        return ESP_FAIL;
    }
    esp_err_t err = esp_http_client_open(client, 0);
    if (err != ESP_OK) {
        esp_http_client_cleanup(client);
        return err;
    }
    int len = esp_http_client_fetch_headers(client);
    if (len < 0) {
        len = 4096;
    }
    size_t cap = (size_t)len + 64;
    char *buf = calloc(1, cap);
    if (!buf) {
        esp_http_client_cleanup(client);
        return ESP_ERR_NO_MEM;
    }
    int read = esp_http_client_read(client, buf, cap - 1);
    esp_http_client_cleanup(client);
    if (read < 0) {
        free(buf);
        return ESP_FAIL;
    }
    buf[read] = '\0';
    *out_body = buf;
    *out_len = read;
    return ESP_OK;
}

esp_err_t slideshow_client_init(const char *base_url)
{
    if (!base_url) {
        return ESP_ERR_INVALID_ARG;
    }
    strncpy(s_base_url, base_url, sizeof(s_base_url) - 1);
    return ESP_OK;
}

static float json_get_double(const cJSON *obj, const char *key, float fallback)
{
    const cJSON *item = cJSON_GetObjectItem(obj, key);
    return cJSON_IsNumber(item) ? (float)item->valuedouble : fallback;
}

static int json_get_int(const cJSON *obj, const char *key, int fallback)
{
    const cJSON *item = cJSON_GetObjectItem(obj, key);
    return cJSON_IsNumber(item) ? item->valueint : fallback;
}

static slide_type_t parse_slide_type(const char *s)
{
    if (!s) {
        return SLIDE_TYPE_WEATHER;
    }
    if (strcmp(s, "image") == 0) {
        return SLIDE_TYPE_IMAGE;
    }
    if (strcmp(s, "ham") == 0) {
        return SLIDE_TYPE_HAM;
    }
    if (strcmp(s, "outlook") == 0) {
        return SLIDE_TYPE_OUTLOOK;
    }
    if (strcmp(s, "ha") == 0) {
        return SLIDE_TYPE_HA;
    }
    return SLIDE_TYPE_WEATHER;
}

static void parse_weather(cJSON *root, weather_data_t *w)
{
    cJSON *wx = cJSON_GetObjectItem(root, "weather");
    if (!cJSON_IsObject(wx)) {
        w->valid = false;
        return;
    }
    w->temperature_f = json_get_double(wx, "temperature_f", 0.f);
    w->feels_like_f = json_get_double(wx, "feels_like_f", 0.f);
    w->humidity_pct = json_get_double(wx, "humidity_pct", 0.f);
    w->wind_mph = json_get_double(wx, "wind_mph", 0.f);
    w->pressure_inhg = json_get_double(wx, "pressure_inhg", 0.f);
    w->uv_index = json_get_double(wx, "uv_index", 0.f);
    const cJSON *wd = cJSON_GetObjectItem(wx, "wind_direction");
    if (cJSON_IsString(wd)) {
        strncpy(w->wind_direction, wd->valuestring, sizeof(w->wind_direction) - 1);
    }
    const cJSON *cond = cJSON_GetObjectItem(wx, "conditions");
    if (cJSON_IsString(cond)) {
        strncpy(w->conditions, cond->valuestring, sizeof(w->conditions) - 1);
    }
    const cJSON *sr = cJSON_GetObjectItem(wx, "sunrise");
    if (cJSON_IsString(sr)) {
        strncpy(w->sunrise, sr->valuestring, sizeof(w->sunrise) - 1);
    }
    const cJSON *ss = cJSON_GetObjectItem(wx, "sunset");
    if (cJSON_IsString(ss)) {
        strncpy(w->sunset, ss->valuestring, sizeof(w->sunset) - 1);
    }
    w->valid = true;
}

static void parse_ham(cJSON *root, ham_data_t *h)
{
    cJSON *ham = cJSON_GetObjectItem(root, "ham");
    if (!cJSON_IsObject(ham)) {
        h->valid = false;
        return;
    }
    h->sfi = json_get_int(ham, "sfi", 0);
    h->k_index = json_get_int(ham, "k_index", 0);
    h->a_index = json_get_int(ham, "a_index", 0);
    const cJSON *sum = cJSON_GetObjectItem(ham, "summary");
    if (cJSON_IsString(sum)) {
        strncpy(h->summary, sum->valuestring, sizeof(h->summary) - 1);
    }
    h->valid = true;
}

esp_err_t slideshow_fetch_manifest(slideshow_manifest_t *out)
{
    if (!out) {
        return ESP_ERR_INVALID_ARG;
    }
    memset(out, 0, sizeof(*out));

    char url[192];
    snprintf(url, sizeof(url), "%s/api/v1/slideshow", s_base_url);

    char *body = NULL;
    int len = 0;
    esp_err_t err = http_get_to_buffer(url, &body, &len);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "manifest fetch failed");
        return err;
    }

    cJSON *root = cJSON_Parse(body);
    free(body);
    if (!root) {
        return ESP_FAIL;
    }

    out->refresh_after_ms =
        (uint32_t)json_get_int(root, "refresh_after_sec", 0) * 1000U;
    cJSON *playback = cJSON_GetObjectItem(root, "playback");
    if (cJSON_IsObject(playback)) {
        out->advance_ms =
            (uint32_t)json_get_int(playback, "advance_sec", 0) * 1000U;
    }
    if (out->advance_ms == 0) {
        out->advance_ms = 10000;
    }

    cJSON *slides = cJSON_GetObjectItem(root, "slides");
    if (cJSON_IsArray(slides)) {
        int n = cJSON_GetArraySize(slides);
        for (int i = 0; i < n && (size_t)i < SLIDESHOW_MAX_SLIDES; i++) {
            cJSON *s = cJSON_GetArrayItem(slides, i);
            slide_def_t *d = &out->slides[out->slide_count++];
            const cJSON *id = cJSON_GetObjectItem(s, "id");
            if (cJSON_IsString(id)) {
                strncpy(d->id, id->valuestring, sizeof(d->id) - 1);
            }
            const cJSON *type_item = cJSON_GetObjectItem(s, "type");
            d->type = parse_slide_type(cJSON_IsString(type_item) ? type_item->valuestring : NULL);
            const cJSON *title = cJSON_GetObjectItem(s, "title");
            if (cJSON_IsString(title)) {
                strncpy(d->title, title->valuestring, sizeof(d->title) - 1);
            }
            const cJSON *u = cJSON_GetObjectItem(s, "url");
            if (cJSON_IsString(u) && u->valuestring) {
                strncpy(d->url, u->valuestring, sizeof(d->url) - 1);
            }
            const cJSON *rev = cJSON_GetObjectItem(s, "revision");
            if (cJSON_IsString(rev)) {
                strncpy(d->revision, rev->valuestring, sizeof(d->revision) - 1);
            }
        }
    }

    parse_weather(root, &out->weather);
    parse_ham(root, &out->ham);

    cJSON *alerts = cJSON_GetObjectItem(root, "alerts");
    if (cJSON_IsArray(alerts)) {
        int n = cJSON_GetArraySize(alerts);
        for (int i = 0; i < n && out->alert_count < SLIDESHOW_MAX_ALERTS; i++) {
            cJSON *a = cJSON_GetArrayItem(alerts, i);
            alert_item_t *item = &out->alerts[out->alert_count++];
            const cJSON *aid = cJSON_GetObjectItem(a, "id");
            if (cJSON_IsString(aid)) {
                strncpy(item->id, aid->valuestring, sizeof(item->id) - 1);
            }
            const cJSON *ev = cJSON_GetObjectItem(a, "event");
            if (cJSON_IsString(ev)) {
                strncpy(item->event, ev->valuestring, sizeof(item->event) - 1);
            }
            const cJSON *up = cJSON_GetObjectItem(a, "updated");
            if (cJSON_IsString(up)) {
                strncpy(item->updated, up->valuestring, sizeof(item->updated) - 1);
            }
        }
    }

    cJSON_Delete(root);
    ESP_LOGI(TAG, "manifest: %u slides, %u alerts", (unsigned)out->slide_count,
             (unsigned)out->alert_count);
    return ESP_OK;
}

esp_err_t slideshow_fetch_image(const char *relative_url, uint8_t **out_buf, size_t *out_len)
{
    if (!relative_url || !out_buf || !out_len) {
        return ESP_ERR_INVALID_ARG;
    }
    char url[256];
    if (relative_url[0] == '/') {
        snprintf(url, sizeof(url), "%s%s", s_base_url, relative_url);
    } else {
        snprintf(url, sizeof(url), "%s/%s", s_base_url, relative_url);
    }
    /* Binary JPEG — read into raw buffer (not null-terminated string). */
    esp_http_client_config_t cfg = { .url = url, .timeout_ms = 20000 };
    esp_http_client_handle_t client = esp_http_client_init(&cfg);
    if (!client) {
        return ESP_FAIL;
    }
    esp_err_t err = esp_http_client_open(client, 0);
    if (err != ESP_OK) {
        esp_http_client_cleanup(client);
        return err;
    }
    esp_http_client_fetch_headers(client);
    int cap = 256 * 1024;
    uint8_t *buf = malloc(cap);
    if (!buf) {
        esp_http_client_cleanup(client);
        return ESP_ERR_NO_MEM;
    }
    int total = 0;
    while (total < cap) {
        int r = esp_http_client_read(client, (char *)buf + total, cap - total);
        if (r <= 0) {
            break;
        }
        total += r;
    }
    esp_http_client_cleanup(client);
    if (total <= 0) {
        free(buf);
        return ESP_FAIL;
    }
    *out_buf = buf;
    *out_len = (size_t)total;
    return ESP_OK;
}

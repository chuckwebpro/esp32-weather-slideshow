#pragma once

#include "esp_err.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SLIDESHOW_MAX_SLIDES 8
#define SLIDESHOW_MAX_URL 192
#define SLIDESHOW_MAX_TITLE 64
#define SLIDESHOW_MAX_ALERTS 16
#define SLIDESHOW_MAX_ALERT_ID 96

typedef enum {
    SLIDE_TYPE_WEATHER = 0,
    SLIDE_TYPE_IMAGE,
    SLIDE_TYPE_HAM,
    SLIDE_TYPE_OUTLOOK,
    SLIDE_TYPE_HA,
} slide_type_t;

typedef struct {
    char id[32];
    slide_type_t type;
    char title[SLIDESHOW_MAX_TITLE];
    char url[SLIDESHOW_MAX_URL];
    char revision[16];
} slide_def_t;

typedef struct {
    float temperature_f;
    float feels_like_f;
    float humidity_pct;
    float wind_mph;
    char wind_direction[8];
    float pressure_inhg;
    float uv_index;
    char conditions[48];
    char sunrise[16];
    char sunset[16];
    bool valid;
} weather_data_t;

typedef struct {
    int sfi;
    int k_index;
    int a_index;
    char summary[64];
    bool valid;
} ham_data_t;

typedef struct {
    char id[SLIDESHOW_MAX_ALERT_ID];
    char event[48];
    char updated[32];
} alert_item_t;

typedef struct {
    slide_def_t slides[SLIDESHOW_MAX_SLIDES];
    size_t slide_count;
    weather_data_t weather;
    ham_data_t ham;
    alert_item_t alerts[SLIDESHOW_MAX_ALERTS];
    size_t alert_count;
    uint32_t refresh_after_ms;
    uint32_t advance_ms;
} slideshow_manifest_t;

esp_err_t slideshow_client_init(const char *base_url);

esp_err_t slideshow_fetch_manifest(slideshow_manifest_t *out);

esp_err_t slideshow_fetch_image(const char *relative_url, uint8_t **out_buf, size_t *out_len);

#ifdef __cplusplus
}
#endif

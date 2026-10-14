#include "image_loader.h"

#include "esp_heap_caps.h"
#include "esp_log.h"
#include <stdlib.h>
#include <string.h>

static const char *TAG = "image_loader";

static uint8_t *s_rgb_buf;
static size_t s_rgb_cap;
static lv_image_dsc_t s_img_dsc;

#if __has_include("esp_jpeg_dec.h")
#include "esp_jpeg_dec.h"
#define SLIDESHOW_HAS_ESP_JPEG 1
#else
#define SLIDESHOW_HAS_ESP_JPEG 0
#endif

esp_err_t slideshow_image_set_jpeg(lv_obj_t *img, const uint8_t *jpeg, size_t jpeg_len)
{
    if (!img || !jpeg || jpeg_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

#if SLIDESHOW_HAS_ESP_JPEG
    esp_jpeg_dec_config_t cfg = DEFAULT_ESP_JPEG_DEC_CONFIG();
    cfg.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;

    esp_jpeg_dec_handle_t dec = NULL;
    esp_err_t err = esp_jpeg_dec_open(&cfg, &dec);
    if (err != ESP_OK) {
        return err;
    }

    jpeg_dec_header_info_t header;
    err = esp_jpeg_dec_parse_header(dec, (uint8_t *)jpeg, jpeg_len, &header);
    if (err != ESP_OK) {
        esp_jpeg_dec_close(dec);
        return err;
    }

    size_t need = (size_t)header.width * header.height * 2;
    if (need > s_rgb_cap) {
        free(s_rgb_buf);
        s_rgb_buf = heap_caps_malloc(need, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
        if (!s_rgb_buf) {
            s_rgb_buf = malloc(need);
        }
        if (!s_rgb_buf) {
            esp_jpeg_dec_close(dec);
            return ESP_ERR_NO_MEM;
        }
        s_rgb_cap = need;
    }

    jpeg_dec_io_t io = {
        .inbuf = (uint8_t *)jpeg,
        .inbuf_len = jpeg_len,
        .outbuf = s_rgb_buf,
        .outbuf_len = need,
    };
    err = esp_jpeg_dec_process(dec, &io);
    esp_jpeg_dec_close(dec);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "jpeg decode failed");
        return err;
    }

    memset(&s_img_dsc, 0, sizeof(s_img_dsc));
    s_img_dsc.header.magic = LV_IMAGE_HEADER_MAGIC;
    s_img_dsc.header.cf = LV_COLOR_FORMAT_RGB565;
    s_img_dsc.header.w = header.width;
    s_img_dsc.header.h = header.height;
    s_img_dsc.header.stride = header.width * 2;
    s_img_dsc.data_size = need;
    s_img_dsc.data = s_rgb_buf;

    lv_image_set_src(img, &s_img_dsc);
    lv_obj_center(img);
    return ESP_OK;
#else
    ESP_LOGW(TAG, "esp_jpeg_dec not available; enable esp_jpeg in IDF");
    (void)jpeg;
    (void)jpeg_len;
    return ESP_ERR_NOT_SUPPORTED;
#endif
}

void slideshow_image_loader_deinit(void)
{
    free(s_rgb_buf);
    s_rgb_buf = NULL;
    s_rgb_cap = 0;
}

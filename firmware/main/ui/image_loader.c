#include "image_loader.h"

#include "esp_heap_caps.h"
#include "esp_log.h"
#include "jpeg_decoder.h"
#include <stdlib.h>
#include <string.h>

static const char *TAG = "image_loader";

static uint8_t *s_rgb_buf;
static size_t s_rgb_cap;
static uint8_t *s_work;
static lv_image_dsc_t s_img_dsc;

/* tjpgd returns JDR_MEM1 (3) when the pool cannot hold a 1024-wide MCU line. */
#define JPEG_WORK_BYTES (48 * 1024)

esp_err_t slideshow_image_set_jpeg(lv_obj_t *img, const uint8_t *jpeg, size_t jpeg_len)
{
    if (!img || !jpeg || jpeg_len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    esp_jpeg_image_cfg_t cfg = {
        .indata = (uint8_t *)jpeg,
        .indata_size = jpeg_len,
        .out_format = JPEG_IMAGE_FORMAT_RGB565,
        .out_scale = JPEG_IMAGE_SCALE_0,
    };

    esp_jpeg_image_output_t info = {0};
    esp_err_t err = esp_jpeg_get_image_info(&cfg, &info);
    if (err != ESP_OK || info.width == 0 || info.height == 0) {
        ESP_LOGE(TAG, "jpeg header failed");
        return err != ESP_OK ? err : ESP_FAIL;
    }

    size_t need = (size_t)info.width * info.height * 2;
    if (info.output_len > need) {
        need = info.output_len;
    }
    if (need > s_rgb_cap) {
        free(s_rgb_buf);
        s_rgb_buf = heap_caps_malloc(need, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
        if (!s_rgb_buf) {
            s_rgb_buf = malloc(need);
        }
        if (!s_rgb_buf) {
            return ESP_ERR_NO_MEM;
        }
        s_rgb_cap = need;
    }

    if (!s_work) {
        s_work = heap_caps_malloc(JPEG_WORK_BYTES, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
        if (!s_work) {
            s_work = malloc(JPEG_WORK_BYTES);
        }
        if (!s_work) {
            return ESP_ERR_NO_MEM;
        }
    }
    cfg.outbuf = s_rgb_buf;
    cfg.outbuf_size = need;
    cfg.advanced.working_buffer = s_work;
    cfg.advanced.working_buffer_size = JPEG_WORK_BYTES;
    esp_jpeg_image_output_t out = {0};
    err = esp_jpeg_decode(&cfg, &out);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "jpeg decode failed");
        return err;
    }

    memset(&s_img_dsc, 0, sizeof(s_img_dsc));
    s_img_dsc.header.magic = LV_IMAGE_HEADER_MAGIC;
    s_img_dsc.header.cf = LV_COLOR_FORMAT_RGB565;
    s_img_dsc.header.w = out.width ? out.width : info.width;
    s_img_dsc.header.h = out.height ? out.height : info.height;
    s_img_dsc.header.stride = s_img_dsc.header.w * 2;
    s_img_dsc.data_size = out.output_len ? out.output_len : need;
    s_img_dsc.data = s_rgb_buf;

    lv_image_set_src(img, &s_img_dsc);
    lv_obj_center(img);
    ESP_LOGI(TAG, "jpeg %ux%u", (unsigned)s_img_dsc.header.w, (unsigned)s_img_dsc.header.h);
    return ESP_OK;
}

void slideshow_image_loader_deinit(void)
{
    free(s_rgb_buf);
    free(s_work);
    s_rgb_buf = NULL;
    s_work = NULL;
    s_rgb_cap = 0;
}

#include "slideshow_ui.h"

#include "image_loader.h"
#include "net/slideshow_client.h"
#include "esp_log.h"
#include <stdlib.h>
#include <string.h>

static const char *TAG = "slideshow_ui";

struct slideshow_ui {
    lv_obj_t *root;
    lv_obj_t *content;
    lv_obj_t *pause_badge;
    lv_obj_t *weather_panel;
    lv_obj_t *ham_panel;
    lv_obj_t *img_widget;
    slideshow_manifest_t manifest;
    size_t current;
    bool paused;
    float zoom;
};

static void fade_pause_cb(lv_timer_t *t)
{
    lv_obj_t *badge = lv_timer_get_user_data(t);
    lv_obj_add_flag(badge, LV_OBJ_FLAG_HIDDEN);
    lv_timer_del(t);
}

static void show_pause_badge(slideshow_ui_t *ui)
{
    lv_obj_clear_flag(ui->pause_badge, LV_OBJ_FLAG_HIDDEN);
    lv_obj_set_style_opa(ui->pause_badge, LV_OPA_COVER, 0);
    lv_timer_create(fade_pause_cb, 1200, ui->pause_badge);
}

static void tap_event_cb(lv_event_t *e)
{
    slideshow_ui_t *ui = lv_event_get_user_data(e);
    ui->paused = !ui->paused;
    if (ui->paused) {
        show_pause_badge(ui);
    } else {
        slideshow_ui_reset_zoom(ui);
    }
}

static void gesture_cb(lv_event_t *e)
{
    slideshow_ui_t *ui = lv_event_get_user_data(e);
    if (!ui->paused || lv_event_get_code(e) != LV_EVENT_GESTURE) {
        return;
    }
    lv_indev_t *indev = lv_indev_active();
    if (!indev) {
        return;
    }
    lv_dir_t dir = lv_indev_get_gesture_dir(indev);
    if (dir == LV_DIR_LEFT) {
        slideshow_ui_next(ui);
    } else if (dir == LV_DIR_RIGHT) {
        slideshow_ui_prev(ui);
    }
}

static void pinch_zoom_cb(lv_event_t *e)
{
    slideshow_ui_t *ui = lv_event_get_user_data(e);
    lv_indev_t *indev = lv_indev_active();
    if (!indev) {
        return;
    }
    lv_dir_t dir = lv_indev_get_gesture_dir(indev);
    (void)dir;
    /* LVGL gesture recognizer scale — use event code when available */
    if (lv_event_get_code(e) == LV_EVENT_GESTURE) {
        float scale = ui->zoom * 1.05f;
        slideshow_ui_apply_pinch_zoom(ui, scale);
    }
}

slideshow_ui_t *slideshow_ui_create(lv_obj_t *root)
{
    slideshow_ui_t *ui = calloc(1, sizeof(*ui));
    if (!ui) {
        return NULL;
    }
    ui->root = root;
    ui->zoom = 1.0f;
    ui->content = lv_obj_create(root);
    lv_obj_set_size(ui->content, LV_PCT(100), LV_PCT(100));
    lv_obj_set_style_pad_all(ui->content, 0, 0);
    lv_obj_set_style_border_width(ui->content, 0, 0);
    lv_obj_remove_flag(ui->content, LV_OBJ_FLAG_SCROLLABLE);

    ui->weather_panel = lv_obj_create(ui->content);
    lv_obj_add_flag(ui->weather_panel, LV_OBJ_FLAG_HIDDEN);
    ui->ham_panel = lv_obj_create(ui->content);
    lv_obj_add_flag(ui->ham_panel, LV_OBJ_FLAG_HIDDEN);
    ui->img_widget = lv_image_create(ui->content);
    lv_obj_add_flag(ui->img_widget, LV_OBJ_FLAG_HIDDEN);

    ui->pause_badge = lv_label_create(root);
    lv_label_set_text(ui->pause_badge, "Paused");
    lv_obj_align(ui->pause_badge, LV_ALIGN_TOP_MID, 0, 8);
    lv_obj_add_flag(ui->pause_badge, LV_OBJ_FLAG_HIDDEN);

    lv_obj_add_event_cb(ui->content, tap_event_cb, LV_EVENT_CLICKED, ui);
    lv_obj_add_flag(ui->content, LV_OBJ_FLAG_GESTURE_BUBBLE);
    lv_obj_add_event_cb(ui->content, gesture_cb, LV_EVENT_GESTURE, ui);
    lv_obj_add_event_cb(ui->content, pinch_zoom_cb, LV_EVENT_GESTURE, ui);

    return ui;
}

void slideshow_ui_set_manifest(slideshow_ui_t *ui, const slideshow_manifest_t *manifest)
{
    if (!ui || !manifest) {
        return;
    }
    ui->manifest = *manifest;
    if (ui->current >= ui->manifest.slide_count) {
        ui->current = 0;
    }
}

static void fill_weather(slideshow_ui_t *ui)
{
    lv_obj_clean(ui->weather_panel);
    lv_obj_clear_flag(ui->weather_panel, LV_OBJ_FLAG_HIDDEN);
    const weather_data_t *w = &ui->manifest.weather;
    if (!w->valid) {
        lv_obj_t *lbl = lv_label_create(ui->weather_panel);
        lv_label_set_text(lbl, "Weather unavailable");
        return;
    }
    char line[128];
    lv_obj_t *title = lv_label_create(ui->weather_panel);
    lv_label_set_text(title, ui->manifest.slides[ui->current].title);
    lv_obj_set_style_text_font(title, &lv_font_montserrat_28, 0);

    lv_obj_t *body = lv_label_create(ui->weather_panel);
    snprintf(line, sizeof(line), "%.0f°F  %s\nFeels %.0f°F",
             w->temperature_f, w->conditions, w->feels_like_f);
    lv_label_set_text(body, line);

    lv_obj_t *meta = lv_label_create(ui->weather_panel);
    snprintf(line, sizeof(line),
             "Humidity %.0f%%  Wind %.0f %s mph\nPressure %.2f in  UV %.0f",
             w->humidity_pct, w->wind_mph, w->wind_direction, w->pressure_inhg, w->uv_index);
    lv_label_set_text(meta, line);
}

static void fill_ham(slideshow_ui_t *ui)
{
    lv_obj_clean(ui->ham_panel);
    lv_obj_clear_flag(ui->ham_panel, LV_OBJ_FLAG_HIDDEN);
    const ham_data_t *h = &ui->manifest.ham;
    lv_obj_t *title = lv_label_create(ui->ham_panel);
    lv_label_set_text(title, "HF Band Conditions");
    if (h->valid) {
        lv_obj_t *body = lv_label_create(ui->ham_panel);
        char line[96];
        snprintf(line, sizeof(line), "%s\nSFI %d  K %d  A %d", h->summary, h->sfi, h->k_index,
                 h->a_index);
        lv_label_set_text(body, line);
    }
}

static esp_err_t load_slide_image(slideshow_ui_t *ui, const slide_def_t *slide)
{
    if (!slide->url[0]) {
        return ESP_ERR_INVALID_ARG;
    }
    uint8_t *buf = NULL;
    size_t len = 0;
    esp_err_t err = slideshow_fetch_image(slide->url, &buf, &len);
    if (err != ESP_OK) {
        return err;
    }
    err = slideshow_image_set_jpeg(ui->img_widget, buf, len);
    free(buf);
    return err;
}

void slideshow_ui_show_slide(slideshow_ui_t *ui, size_t index)
{
    if (!ui || ui->manifest.slide_count == 0) {
        return;
    }
    if (index >= ui->manifest.slide_count) {
        index = 0;
    }
    ui->current = index;
    slideshow_ui_reset_zoom(ui);

    lv_obj_add_flag(ui->weather_panel, LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(ui->ham_panel, LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(ui->img_widget, LV_OBJ_FLAG_HIDDEN);

    const slide_def_t *slide = &ui->manifest.slides[index];
    switch (slide->type) {
    case SLIDE_TYPE_WEATHER:
        fill_weather(ui);
        break;
    case SLIDE_TYPE_HAM:
        fill_ham(ui);
        break;
    case SLIDE_TYPE_IMAGE:
    case SLIDE_TYPE_OUTLOOK:
        lv_obj_clear_flag(ui->img_widget, LV_OBJ_FLAG_HIDDEN);
        if (load_slide_image(ui, slide) != ESP_OK) {
            ESP_LOGW(TAG, "image load failed for %s", slide->id);
        }
        break;
    default:
        break;
    }
}

size_t slideshow_ui_current_index(const slideshow_ui_t *ui)
{
    return ui ? ui->current : 0;
}

size_t slideshow_ui_slide_count(const slideshow_ui_t *ui)
{
    return ui ? ui->manifest.slide_count : 0;
}

bool slideshow_ui_is_paused(const slideshow_ui_t *ui)
{
    return ui && ui->paused;
}

void slideshow_ui_set_paused(slideshow_ui_t *ui, bool paused)
{
    if (ui) {
        ui->paused = paused;
    }
}

void slideshow_ui_next(slideshow_ui_t *ui)
{
    if (!ui || ui->manifest.slide_count == 0) {
        return;
    }
    ui->current = (ui->current + 1) % ui->manifest.slide_count;
    slideshow_ui_show_slide(ui, ui->current);
}

void slideshow_ui_prev(slideshow_ui_t *ui)
{
    if (!ui || ui->manifest.slide_count == 0) {
        return;
    }
    ui->current = (ui->current + ui->manifest.slide_count - 1) % ui->manifest.slide_count;
    slideshow_ui_show_slide(ui, ui->current);
}

void slideshow_ui_reset_zoom(slideshow_ui_t *ui)
{
    if (!ui) {
        return;
    }
    ui->zoom = 1.0f;
    lv_image_set_scale(ui->img_widget, 256);
    lv_obj_set_style_transform_zoom(ui->img_widget, 256, 0);
}

void slideshow_ui_apply_pinch_zoom(slideshow_ui_t *ui, float scale)
{
    if (!ui) {
        return;
    }
    if (scale < 1.0f) {
        scale = 1.0f;
    }
    if (scale > 3.0f) {
        scale = 3.0f;
    }
    ui->zoom = scale;
    uint16_t z = (uint16_t)(256 * scale);
    lv_image_set_scale(ui->img_widget, z);
}

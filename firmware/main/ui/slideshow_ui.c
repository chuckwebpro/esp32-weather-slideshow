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

static void style_text_panel(lv_obj_t *panel)
{
    lv_obj_set_size(panel, LV_PCT(100), LV_PCT(100));
    lv_obj_set_style_bg_opa(panel, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(panel, 0, 0);
    lv_obj_set_style_pad_all(panel, 36, 0);
    lv_obj_set_style_pad_row(panel, 18, 0);
    lv_obj_set_flex_flow(panel, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(panel, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_START);
    lv_obj_set_scrollable(panel, false);
}

static void style_label(lv_obj_t *lbl, const lv_font_t *font)
{
    lv_obj_set_width(lbl, LV_PCT(100));
    lv_label_set_long_mode(lbl, LV_LABEL_LONG_WRAP);
    if (font) {
        lv_obj_set_style_text_font(lbl, font, 0);
    }
}

static void fade_pause_cb(lv_timer_t *t)
{
    lv_obj_t *badge = lv_timer_get_user_data(t);
    lv_obj_set_hidden(badge, true);
    lv_timer_del(t);
}

static void show_pause_badge(slideshow_ui_t *ui)
{
    lv_obj_set_hidden(ui->pause_badge, false);
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
    lv_obj_set_style_bg_color(root, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(root, LV_OPA_COVER, 0);

    ui->content = lv_obj_create(root);
    lv_obj_set_size(ui->content, LV_PCT(100), LV_PCT(100));
    lv_obj_set_style_bg_color(ui->content, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(ui->content, LV_OPA_COVER, 0);
    lv_obj_set_style_text_color(ui->content, lv_color_white(), 0);
    lv_obj_set_style_pad_all(ui->content, 0, 0);
    lv_obj_set_style_border_width(ui->content, 0, 0);
    lv_obj_set_scrollable(ui->content, false);

    ui->weather_panel = lv_obj_create(ui->content);
    style_text_panel(ui->weather_panel);
    lv_obj_set_hidden(ui->weather_panel, true);
    ui->ham_panel = lv_obj_create(ui->content);
    style_text_panel(ui->ham_panel);
    lv_obj_set_hidden(ui->ham_panel, true);
    ui->img_widget = lv_image_create(ui->content);
    lv_obj_set_size(ui->img_widget, LV_PCT(100), LV_PCT(100));
    lv_obj_set_hidden(ui->img_widget, true);

    ui->pause_badge = lv_label_create(root);
    lv_label_set_text(ui->pause_badge, "Paused");
    lv_obj_align(ui->pause_badge, LV_ALIGN_TOP_MID, 0, 8);
    lv_obj_set_hidden(ui->pause_badge, true);

    lv_obj_add_event_cb(ui->content, tap_event_cb, LV_EVENT_CLICKED, ui);
    lv_obj_set_gesture_bubble(ui->content, true);
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

static lv_obj_t *add_stat(lv_obj_t *row, const char *caption, const char *value)
{
    lv_obj_t *card = lv_obj_create(row);
    lv_obj_set_height(card, 148);
    lv_obj_set_flex_grow(card, 1);
    lv_obj_set_style_bg_color(card, lv_color_hex(0x1C1C1C), 0);
    lv_obj_set_style_bg_opa(card, LV_OPA_COVER, 0);
    lv_obj_set_style_radius(card, 16, 0);
    lv_obj_set_style_border_width(card, 0, 0);
    lv_obj_set_style_pad_all(card, 18, 0);
    lv_obj_set_style_pad_row(card, 8, 0);
    lv_obj_set_flex_flow(card, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(card, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_START);
    lv_obj_set_scrollable(card, false);

    lv_obj_t *cap = lv_label_create(card);
    lv_label_set_text(cap, caption);
    lv_obj_set_style_text_font(cap, &lv_font_montserrat_20, 0);
    lv_obj_set_style_text_color(cap, lv_color_hex(0x9AA0A6), 0);

    lv_obj_t *val = lv_label_create(card);
    lv_label_set_text(val, value);
    lv_obj_set_style_text_font(val, &lv_font_montserrat_28, 0);
    lv_obj_set_style_text_color(val, lv_color_white(), 0);
    return card;
}

static lv_obj_t *add_stat_row(lv_obj_t *parent)
{
    lv_obj_t *row = lv_obj_create(parent);
    lv_obj_set_width(row, LV_PCT(100));
    lv_obj_set_height(row, 168);
    lv_obj_set_style_bg_opa(row, LV_OPA_TRANSP, 0);
    lv_obj_set_style_border_width(row, 0, 0);
    lv_obj_set_style_pad_all(row, 0, 0);
    lv_obj_set_style_pad_column(row, 16, 0);
    lv_obj_set_flex_flow(row, LV_FLEX_FLOW_ROW);
    lv_obj_set_scrollable(row, false);
    return row;
}

static void fill_weather(slideshow_ui_t *ui)
{
    lv_obj_clean(ui->weather_panel);
    lv_obj_set_hidden(ui->weather_panel, false);
    const weather_data_t *w = &ui->manifest.weather;
    if (!w->valid) {
        lv_obj_t *lbl = lv_label_create(ui->weather_panel);
        style_label(lbl, &lv_font_montserrat_28);
        lv_label_set_text(lbl, "Weather unavailable");
        return;
    }
    char line[64];
    const char *title = ui->manifest.slides[ui->current].title;
    lv_obj_t *heading = lv_label_create(ui->weather_panel);
    style_label(heading, &lv_font_montserrat_20);
    lv_obj_set_style_text_color(heading, lv_color_hex(0x9AA0A6), 0);
    lv_label_set_text(heading, title[0] ? title : "Current Weather");

    lv_obj_t *temp = lv_label_create(ui->weather_panel);
    style_label(temp, &lv_font_montserrat_48);
    snprintf(line, sizeof(line), "%.0f F", w->temperature_f);
    lv_label_set_text(temp, line);

    lv_obj_t *cond = lv_label_create(ui->weather_panel);
    style_label(cond, &lv_font_montserrat_28);
    lv_label_set_text(cond, w->conditions[0] ? w->conditions : "Conditions unavailable");

    lv_obj_t *feels = lv_label_create(ui->weather_panel);
    style_label(feels, &lv_font_montserrat_20);
    lv_obj_set_style_text_color(feels, lv_color_hex(0x9AA0A6), 0);
    snprintf(line, sizeof(line), "Feels like %.0f F", w->feels_like_f);
    lv_label_set_text(feels, line);

    lv_obj_t *row = add_stat_row(ui->weather_panel);
    snprintf(line, sizeof(line), "%.0f%%", w->humidity_pct);
    add_stat(row, "Humidity", line);
    if (w->wind_direction[0]) {
        snprintf(line, sizeof(line), "%.0f %s", w->wind_mph, w->wind_direction);
    } else {
        snprintf(line, sizeof(line), "%.0f mph", w->wind_mph);
    }
    add_stat(row, "Wind", line);
    snprintf(line, sizeof(line), "%.2f in", w->pressure_inhg);
    add_stat(row, "Pressure", line);
    snprintf(line, sizeof(line), "%.0f", w->uv_index);
    add_stat(row, "UV", line);
}

static void fill_ham(slideshow_ui_t *ui)
{
    lv_obj_clean(ui->ham_panel);
    lv_obj_set_hidden(ui->ham_panel, false);
    const ham_data_t *h = &ui->manifest.ham;
    lv_obj_t *heading = lv_label_create(ui->ham_panel);
    style_label(heading, &lv_font_montserrat_20);
    lv_obj_set_style_text_color(heading, lv_color_hex(0x9AA0A6), 0);
    lv_label_set_text(heading, "HF Band Conditions");

    lv_obj_t *summary = lv_label_create(ui->ham_panel);
    style_label(summary, &lv_font_montserrat_36);
    lv_label_set_text(summary, (h->valid && h->summary[0]) ? h->summary : "Unavailable");

    if (!h->valid) {
        return;
    }
    char line[24];
    lv_obj_t *row = add_stat_row(ui->ham_panel);
    snprintf(line, sizeof(line), "%d", h->sfi);
    add_stat(row, "Solar flux", line);
    snprintf(line, sizeof(line), "%d", h->k_index);
    add_stat(row, "K index", line);
    snprintf(line, sizeof(line), "%d", h->a_index);
    add_stat(row, "A index", line);
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

    lv_obj_set_hidden(ui->weather_panel, true);
    lv_obj_set_hidden(ui->ham_panel, true);
    lv_obj_set_hidden(ui->img_widget, true);

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
        lv_obj_set_hidden(ui->img_widget, false);
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

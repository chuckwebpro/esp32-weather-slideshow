#pragma once

#include "net/slideshow_client.h"
#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct slideshow_ui slideshow_ui_t;

slideshow_ui_t *slideshow_ui_create(lv_obj_t *root);

void slideshow_ui_set_manifest(slideshow_ui_t *ui, const slideshow_manifest_t *manifest);

void slideshow_ui_show_slide(slideshow_ui_t *ui, size_t index);

size_t slideshow_ui_slide_count(const slideshow_ui_t *ui);

bool slideshow_ui_is_paused(const slideshow_ui_t *ui);

void slideshow_ui_set_paused(slideshow_ui_t *ui, bool paused);

void slideshow_ui_next(slideshow_ui_t *ui);

void slideshow_ui_prev(slideshow_ui_t *ui);

void slideshow_ui_reset_zoom(slideshow_ui_t *ui);

void slideshow_ui_apply_pinch_zoom(slideshow_ui_t *ui, float scale);

#ifdef __cplusplus
}
#endif

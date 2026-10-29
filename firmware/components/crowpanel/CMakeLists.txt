idf_component_register(
    SRCS "crowpanel_board.c"
    INCLUDE_DIRS "include"
    REQUIRES driver esp_hw_support esp_lvgl_port bsp_display bsp_i2c
)

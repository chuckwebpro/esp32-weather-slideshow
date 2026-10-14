#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Init STA, connect using menuconfig SSID/password, block until IP or timeout. */
esp_err_t wifi_sta_connect(void);

#ifdef __cplusplus
}
#endif

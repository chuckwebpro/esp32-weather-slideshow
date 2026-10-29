#include "wifi_sta.h"

#include "sdkconfig.h"

#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include <string.h>

static const char *TAG = "wifi_sta";

#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT BIT1
#define NVS_NS "slideshow"

static EventGroupHandle_t s_wifi_events;
static char s_ssid[32];
static char s_pass[64];

static bool nvs_load_wifi(void)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) {
        return false;
    }
    size_t ssid_len = sizeof(s_ssid);
    size_t pass_len = sizeof(s_pass);
    esp_err_t ssid_err = nvs_get_str(h, "wifi_ssid", s_ssid, &ssid_len);
    esp_err_t pass_err = nvs_get_str(h, "wifi_pass", s_pass, &pass_len);
    nvs_close(h);
    return ssid_err == ESP_OK && pass_err == ESP_OK && s_ssid[0] != '\0';
}

static void nvs_save_wifi(void)
{
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READWRITE, &h) != ESP_OK) {
        ESP_LOGW(TAG, "could not store WiFi in NVS");
        return;
    }
    nvs_set_str(h, "wifi_ssid", s_ssid);
    nvs_set_str(h, "wifi_pass", s_pass);
    nvs_commit(h);
    nvs_close(h);
    ESP_LOGI(TAG, "stored WiFi SSID in NVS");
}

/* Menuconfig wins when it is a real network. The placeholder must not erase NVS. */
static void select_wifi_credentials(void)
{
    const bool menu_is_real = strcmp(CONFIG_SLIDESHOW_WIFI_SSID, "your-ssid") != 0;
    char saved_ssid[sizeof(s_ssid)] = {0};
    char saved_pass[sizeof(s_pass)] = {0};
    bool have_nvs = false;

    if (nvs_load_wifi()) {
        have_nvs = true;
        memcpy(saved_ssid, s_ssid, sizeof(saved_ssid));
        memcpy(saved_pass, s_pass, sizeof(saved_pass));
    }

    if (menu_is_real &&
        (!have_nvs || strcmp(CONFIG_SLIDESHOW_WIFI_SSID, saved_ssid) != 0 ||
         strcmp(CONFIG_SLIDESHOW_WIFI_PASSWORD, saved_pass) != 0)) {
        strlcpy(s_ssid, CONFIG_SLIDESHOW_WIFI_SSID, sizeof(s_ssid));
        strlcpy(s_pass, CONFIG_SLIDESHOW_WIFI_PASSWORD, sizeof(s_pass));
        nvs_save_wifi();
        return;
    }
    if (have_nvs) {
        memcpy(s_ssid, saved_ssid, sizeof(s_ssid));
        memcpy(s_pass, saved_pass, sizeof(s_pass));
        ESP_LOGI(TAG, "using WiFi SSID saved on the board");
        return;
    }
    strlcpy(s_ssid, CONFIG_SLIDESHOW_WIFI_SSID, sizeof(s_ssid));
    strlcpy(s_pass, CONFIG_SLIDESHOW_WIFI_PASSWORD, sizeof(s_pass));
    ESP_LOGW(TAG, "WiFi SSID is still the menuconfig placeholder");
}

static void wifi_event_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupSetBits(s_wifi_events, WIFI_FAIL_BIT);
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(s_wifi_events, WIFI_CONNECTED_BIT);
    }
}

esp_err_t wifi_sta_connect(void)
{
    s_wifi_events = xEventGroupCreate();
    if (!s_wifi_events) {
        return ESP_ERR_NO_MEM;
    }

    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t err = esp_wifi_init(&cfg);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_init failed: %s (ESP-Hosted link / SDIO pins?)", esp_err_to_name(err));
        return err;
    }

    esp_event_handler_instance_t inst_wifi;
    esp_event_handler_instance_t inst_ip;
    err = esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event_handler, NULL, &inst_wifi);
    if (err != ESP_OK) {
        return err;
    }
    err = esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL, &inst_ip);
    if (err != ESP_OK) {
        return err;
    }

    select_wifi_credentials();

    wifi_config_t wifi_cfg = {0};
    strlcpy((char *)wifi_cfg.sta.ssid, s_ssid, sizeof(wifi_cfg.sta.ssid));
    strlcpy((char *)wifi_cfg.sta.password, s_pass, sizeof(wifi_cfg.sta.password));
    wifi_cfg.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    err = esp_wifi_set_mode(WIFI_MODE_STA);
    if (err != ESP_OK) {
        return err;
    }
    err = esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg);
    if (err != ESP_OK) {
        return err;
    }
    err = esp_wifi_start();
    if (err != ESP_OK) {
        return err;
    }

    EventBits_t bits = xEventGroupWaitBits(
        s_wifi_events, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT, pdFALSE, pdFALSE,
        pdMS_TO_TICKS(30000));

    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "connected to %s (hostname brain)", s_ssid);
        return ESP_OK;
    }

    ESP_LOGE(TAG, "failed to connect to %s within 30s", s_ssid);
    return ESP_ERR_TIMEOUT;
}

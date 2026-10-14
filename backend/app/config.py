from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: str = "/data"  # env: DATA_DIR
    host: str = "0.0.0.0"
    port: int = 8080

    slideshow_lat: float = 33.20
    slideshow_lon: float = -96.70
    timezone: str = "America/Chicago"

    refresh_after_sec: int = 45
    playback_advance_sec: int = 10

    # NWS user-agent (required by api.weather.gov)
    nws_user_agent: str = "(esp32-weather-slideshow, contact@local)"

    # Output image size (CrowPanel 10.1")
    image_width: int = 1024
    image_height: int = 600

    # Radar crop bbox (lon_w, lat_s, lon_e, lat_n) — Collin County / KFWS AOI
    radar_bbox: tuple[float, float, float, float] = (-96.95, 33.00, -96.45, 33.55)

    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    nws_alerts_url: str = "https://api.weather.gov/alerts/active"
    hamqsl_url: str = "https://www.hamqsl.com/solarxml.php"
    spc_day1_cat_url: str = (
        "https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson"
    )
    us_states_geojson_url: str = (
        "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
    )

    # NOAA Ridge standard products (KFWS); velocity lives under base_velocity/
    ridge_reflectivity_url: str = (
        "https://radar.weather.gov/ridge/standard/KFWS_0.gif"
    )
    ridge_velocity_url: str = (
        "https://radar.weather.gov/ridge/standard/base_velocity/KFWS_0.gif"
    )


settings = Settings()

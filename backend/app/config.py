from pydantic import field_validator
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

    # KFWS radar site (Fort Worth) — Ridge GIF projection center
    ridge_site_lat: float = 32.573
    ridge_site_lon: float = -97.303
    # ~124 nm standard product radius
    ridge_range_km: float = 230.0

    # Radar crop bbox (lon_w, lat_s, lon_e, lat_n) — NE DFW / Collin (see pre-plan AOI)
    radar_bbox: tuple[float, float, float, float] = (-97.08, 32.78, -96.28, 33.82)
    # Fine-tune crop vs Ridge alignment (10 mi ≈ 16.093 km east)
    ridge_offset_km_east: float = 16.093
    ridge_offset_km_north: float = 0.0

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

    @field_validator("radar_bbox", mode="before")
    @classmethod
    def parse_radar_bbox(cls, value: object) -> object:
        if isinstance(value, str):
            parts = [float(x.strip()) for x in value.split(",")]
            if len(parts) != 4:
                raise ValueError("radar_bbox needs four comma-separated numbers")
            return tuple(parts)
        return value


settings = Settings()

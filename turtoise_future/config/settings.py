"""Application settings using Pydantic"""

from enum import Enum
from pydantic import BaseModel, Field


class Mode(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class Resolution(str, Enum):
    MINUTE_1 = "1MIN"
    MINUTE_5 = "5MIN"
    MINUTE_15 = "15MIN"
    MINUTE_30 = "30MIN"
    HOUR_1 = "1HOUR"
    DAY_1 = "1DAY"


class Settings(BaseModel):
    """Application settings"""

    # Mode
    mode: Mode = Field(default=Mode.DEVELOPMENT, description="Run mode")

    # Pipeline flags
    find_cointegrated: bool = Field(default=True, description="Find cointegrated pairs")
    place_trades: bool = Field(default=True, description="Place trades")
    manage_exits: bool = Field(default=True, description="Manage trade exits")
    prepare_data: bool = Field(default=True, description="Prepare supervised learning data")
    generate_model: bool = Field(default=True, description="Generate ML models")

    # Data settings
    resolution: Resolution = Field(default=Resolution.DAY_1, description="Data resolution")
    window: int = Field(default=21, description="Z-score calculation window")
    max_half_life: int = Field(default=24, description="Maximum half-life for pairs")

    # Trading thresholds
    zscore_threshold: float = Field(default=1.5, description="Z-score entry threshold")
    half_life_threshold: int = Field(default=8, description="Half-life threshold")
    usd_per_trade: float = Field(default=50000, description="USD amount per trade")
    usd_min_collateral: float = Field(default=1880, description="Minimum collateral required")

    # Exit settings
    close_at_zscore_cross: bool = Field(default=True, description="Close at Z-score cross")

    # ML settings
    one_percent_threshold: int = Field(default=10000, description="1% position threshold")
    train_threshold: int = Field(default=1200, description="Minimum training samples")

    class Config:
        use_enum_values = True


# Global settings instance
settings = Settings()

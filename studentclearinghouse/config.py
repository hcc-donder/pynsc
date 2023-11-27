import os
from os.path import exists
from typing import Any, List, Optional

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, BaseSettings, Field
from pydantic.env_settings import SettingsSourceCallable


def yml_config_setting(settings: BaseSettings) -> dict[str, Any]:
    config = {
        "CCDW_CFG_FULL_PATH": "",
        "CCDW_CFG_PATH": ".",
        "CCDW_CFG_FN": "config.yml",
        "NSC_CFG_FULL_PATH": "",
        "NSC_CFG_PATH": ".",
        "NSC_CFG_FN": "config.yml",
        **os.environ,
        **dotenv_values("CCDW_CFG_FULL_PATH"),
        **dotenv_values("CCDW_CFG_PATH"),
        **dotenv_values("CCDW_CFG_FN"),
        **dotenv_values("NSC_CFG_FULL_PATH"),
        **dotenv_values("NSC_CFG_PATH"),
        **dotenv_values("NSC_CFG_FN"),
    }

    if config["NSC_CFG_FULL_PATH"] != "":
        config_file = config["NSC_CFG_FULL_PATH"]

    elif config["NSC_CFG_FN"] != "":
        if config["NSC_CFG_PATH"] != "":
            config_file = os.path.join(
                config["NSC_CFG_PATH"], config["NSC_CFG_FN"]
            )
        else:
            config_file = os.path.join(".", config["NSC_CFG_FN"])

    elif config["NSC_CFG_PATH"] != "":
        config_file = os.path.join(config["NSC_CFG_PATH"], "config.yml")

    elif config["CCDW_CFG_FULL_PATH"] != "":
        config_file = config["CCDW_CFG_FULL_PATH"]

    elif config["CCDW_CFG_FN"] != "":
        if config["CCDW_CFG_PATH"] != "":
            config_file = os.path.join(
                config["CCDW_CFG_PATH"], config["CCDW_CFG_FN"]
            )
        else:
            config_file = os.path.join(".", config["CCDW_CFG_FN"])

    elif config["CCDW_CFG_PATH"] != "":
        config_file = os.path.join(config["NSC_CFG_PATH"], "config.yml")

    else:
        config_file = os.path.join(".", "config.yml")

    if exists(config_file):
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f)
        config_dict["config"]["location"] = config_file
    else:
        config_dict = {}
    return config_dict


class SchoolModel(BaseModel):
    name: Optional[str] = ""
    abbrev: Optional[str] = ""
    ipeds: Optional[str] = ""
    fice: Optional[str] = ""
    usgov: Optional[int] = None
    ncccs: Optional[int] = None
    instid: Optional[str] = ""
    inststate: Optional[str] = ""
    instcountry: Optional[str] = ""
    branch: Optional[str] = ""


class ConfigModel(BaseSettings):
    location: Optional[str] = Field(env="CCDW_CFG_FULL_PATH")
    location_fn: Optional[str] = Field(env="CCDW_CFG_FN")
    location_path: Optional[str] = Field(env="CCDW_CFG_PATH")


class Settings(BaseSettings):
    school: Optional[SchoolModel] = SchoolModel()
    config: Optional[ConfigModel] = ConfigModel()

    class Config:
        env_file: str = ".env"
        case_sensitive: bool = False
        arbitrary_types_allowed: bool = True
        validate_all: bool = False

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                env_settings,
                yml_config_setting,
            )


if __name__ == "__main__":
    testdict = Settings().dict()

    print(testdict)
    print("Done")

import copy
import os
import typing as ty

# TODO:rename to config_helper.py


def update_config_from_env[
    T: dict[str, ty.Any]
](config_data: T, prefix: str = "", delimiter: str = "__") -> T:
    updated_config = copy.deepcopy(config_data)
    null = object()

    for key, value in updated_config.items():
        env_key = f"{prefix}{key}"

        if isinstance(value, dict):
            updated_config[key] = update_config_from_env(
                value, env_key + delimiter, delimiter
            )
        else:
            env_value = os.environ.get(env_key, null)
            if env_value is not null:
                updated_config[key] = env_value
    return updated_config

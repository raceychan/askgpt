import copy
import os


def update_config_from_env[
    T: dict
](config_data: T, prefix: str = "", delimiter: str = "__") -> T:
    updated_config = copy.deepcopy(config_data)
    null = object()

    for key, value in updated_config.items():
        # Use the original key case for nested dictionaries
        nested_prefix = f"{prefix}{key}{delimiter}"

        # Use uppercase for environment variable names
        env_key = f"{prefix}{key}"  # .upper()

        if isinstance(value, dict):
            updated_config[key] = update_config_from_env(
                value, nested_prefix, delimiter
            )
        else:
            env_value = os.environ.get(env_key, null)
            if env_value is not null:
                updated_config[key] = env_value
    return updated_config

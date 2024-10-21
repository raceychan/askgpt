import datetime
import typing as ty

import jose.constants

UTC_TZ = datetime.UTC

type SupportedGPTs = ty.Literal["openai", "askgpt_test", "anthropic"]
type SUPPORTED_ALGORITHMS = ty.Literal[tuple(jose.constants.ALGORITHMS.SUPPORTED)]  # type: ignore

"""
Custom types and helpers, do not import any non-builtin here.
"""
import typing as ty


class _NotGiven:
    ...


NOT_GIVEN = _NotGiven()

# use as default value for str, singleton
EMPTY_STR: ty.Annotated[str, "EMPTY_STR"] = ""

# Where None does not mean default value, but a valid value to be set
type Nullable[T] = T | _NotGiven | None


class TimeScale:
    "A more type-aware approach to time scale"
    Second = ty.NewType("Second", int)
    Minute = ty.NewType("Minute", int)
    Hour = ty.NewType("Hour", int)
    Day = ty.NewType("Day", int)
    Week = ty.NewType("Week", int)

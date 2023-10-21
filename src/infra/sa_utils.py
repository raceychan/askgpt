import sqlalchemy as sa
from sqlalchemy.sql import type_api as sa_ty


def as_sa_types(py_type: type) -> sa_ty.TypeEngine:
    import datetime
    import decimal
    import uuid

    TYPES_MAPPING = {
        str: sa.String,
        int: sa.Integer,
        datetime.datetime: sa.DateTime,
        bool: sa.Boolean,
        float: sa.Float,
        list: sa.JSON,
        dict: sa.JSON,
        uuid.UUID: sa.UUID,
        None: sa.Null,
        decimal.Decimal: sa.Numeric,
    }

    return TYPES_MAPPING[py_type]

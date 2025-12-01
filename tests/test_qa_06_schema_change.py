import pandas as pd
import pytest

from alpha_scanner.data_snapshot import SchemaDefinition, validate_schema


def test_qa06_schema_change_negative():
    """
    QA-06: Schema Change (Negative)

    Changing a column name or dtype should cause schema validation to
    fail.
    """
    schema = SchemaDefinition(dtypes={"close": "float64", "volume": "int64"})

    # Case 1: wrong column name
    df_bad_col = pd.DataFrame(
        {"close": [1.0, 2.0], "VLM": [100, 200]},
    )
    df_bad_col["VLM"] = df_bad_col["VLM"].astype("int64")

    with pytest.raises(ValueError):
        validate_schema(df_bad_col, schema)

    # Case 2: wrong dtype
    df_bad_dtype = pd.DataFrame({"close": [1.0, 2.0], "volume": [100.0, 200.0]})

    with pytest.raises(ValueError):
        validate_schema(df_bad_dtype, schema)



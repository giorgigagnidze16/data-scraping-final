import math

import numpy as np
import pandas as pd


def sanitize_reports_for_json(obj):
    if isinstance(obj, dict):
        return {sanitize_reports_for_json(k): sanitize_reports_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_reports_for_json(i) for i in obj]
    elif isinstance(obj, tuple):
        return [sanitize_reports_for_json(i) for i in obj]
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    else:
        return obj

def sanitize_db_for_json(obj):
    """Recursively replace NaN, Inf, -Inf with None, and convert DataFrames to records."""
    if isinstance(obj, pd.DataFrame):
        return sanitize_db_for_json(obj.to_dict(orient="records"))
    elif isinstance(obj, dict):
        return {k: sanitize_db_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_db_for_json(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        else:
            return obj
    elif isinstance(obj, (np.floating, np.integer)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        else:
            return float(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    else:
        return obj


def convert_tuple_keys_to_str(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if isinstance(k, tuple):
                k = "_".join(str(ki) for ki in k)
            new_dict[str(k)] = convert_tuple_keys_to_str(v)
        return new_dict
    elif isinstance(obj, list):
        return [convert_tuple_keys_to_str(i) for i in obj]
    else:
        return obj

import json

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("report")


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {sanitize_for_json(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, tuple):
        return [sanitize_for_json(i) for i in obj]
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


class ReportGenerator:
    def __init__(self, df: pd.DataFrame, stats, trends):
        self.df = df
        self.stats = stats
        self.trends = trends

    def to_json(self, filepath):
        def stringify_tuple_keys(obj):
            if isinstance(obj, dict):
                return {str(k) if isinstance(k, tuple) else k: stringify_tuple_keys(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [stringify_tuple_keys(i) for i in obj]
            else:
                return obj

        report = {
            "statistics": self.stats,
            "trends": {k: v.to_dict(orient='records') if isinstance(v, pd.DataFrame) else v for k, v in
                       self.trends.items()}
        }
        report = sanitize_for_json(stringify_tuple_keys(report))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved as JSON: {filepath}")

    def to_csv(self, filepath):
        self.df.to_csv(filepath, index=False)
        logger.info(f"DataFrame saved as CSV: {filepath}")

    def print_report(self):
        def stringify_tuple_keys(obj):
            if isinstance(obj, dict):
                return {str(k) if isinstance(k, tuple) else k: stringify_tuple_keys(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [stringify_tuple_keys(i) for i in obj]
            else:
                return obj

        safe_stats = sanitize_for_json(stringify_tuple_keys(self.stats))
        logger.info(json.dumps(safe_stats, indent=2))

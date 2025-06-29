import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

import numpy as np
import pandas as pd

from src.analysis.reports import ReportGenerator, sanitize_for_json


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "price": [1.0, 2.0, 3.0],
            "date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]
        })
        self.stats = {
            ('mean', 'cat1'): np.float64(1.5),
            ('count', 'cat1'): np.int64(2),
            'simple': {'x': np.float64(5.5)}
        }
        self.trends = {
            "price_trend": pd.DataFrame({
                "category": ["A", "B"],
                "mean": [100, 200]
            }),
            "other_trend": "just_a_string"
        }
        self.report = ReportGenerator(self.df, self.stats, self.trends)

    def test_sanitize_for_json(self):
        self.assertEqual(sanitize_for_json(np.int32(5)), 5)
        self.assertEqual(sanitize_for_json(np.float32(2.5)), 2.5)
        self.assertEqual(sanitize_for_json(np.array([1, 2, 3])), [1, 2, 3])
        self.assertEqual(sanitize_for_json(pd.Timestamp("2024-06-01")), "2024-06-01T00:00:00")
        self.assertEqual(sanitize_for_json([np.int32(2), np.float64(3.5)]), [2, 3.5])

    def test_stringify_tuple_keys(self):
        def stringify_tuple_keys(obj):
            if isinstance(obj, dict):
                return {str(k) if isinstance(k, tuple) else k: stringify_tuple_keys(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [stringify_tuple_keys(i) for i in obj]
            else:
                return obj

        obj = {(1, 2): "tuple_key", "a": 1}
        result = stringify_tuple_keys(obj)
        self.assertIn("(1, 2)", result)
        self.assertIn("a", result)
        self.assertEqual(result["(1, 2)"], "tuple_key")
        self.assertEqual(result["a"], 1)

    @patch("src.analysis.reports.open", new_callable=mock_open)
    @patch("src.analysis.reports.logger")
    def test_to_json(self, mock_logger, mock_file):
        tmpfile = "test_report.json"
        self.report.to_json(tmpfile)
        mock_file.assert_called_with(tmpfile, "w", encoding="utf-8")
        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        parsed = json.loads(written)
        self.assertIn("statistics", parsed)
        self.assertIn("trends", parsed)
        self.assertIsInstance(parsed["trends"]["price_trend"], list)
        self.assertTrue(all(isinstance(row, dict) for row in parsed["trends"]["price_trend"]))
        self.assertTrue(any("('mean', 'cat1')" in k or "('count', 'cat1')" in k for k in parsed["statistics"].keys()))
        mock_logger.info.assert_any_call(f"Report saved as JSON: {tmpfile}")

    @patch("src.analysis.reports.logger")
    def test_to_csv(self, mock_logger):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            filepath = tmp.name
        try:
            self.report.to_csv(filepath)
            df_loaded = pd.read_csv(filepath, parse_dates=["date"])  # <--- FIXED
            pd.testing.assert_frame_equal(df_loaded, self.df)
            mock_logger.info.assert_any_call(f"DataFrame saved as CSV: {filepath}")
        finally:
            os.remove(filepath)

    @patch("src.analysis.reports.logger")
    def test_print_report(self, mock_logger):
        self.report.print_report()
        args_list = mock_logger.info.call_args_list
        self.assertTrue(any(isinstance(args[0][0], str) and '{' in args[0][0] for args in args_list))


if __name__ == "__main__":
    unittest.main()

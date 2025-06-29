import unittest

import pandas as pd

from src.analysis.statistics import StatisticsEngine


class TestStatisticsEngine(unittest.TestCase):

    def setUp(self):
        self.minimal_numeric_df = pd.DataFrame({
            "price": [1.0, 2.0, 3.0, 4.0],
            "rating": [5, 5, 4, 4],
            "review_count": [10, 20, 30, 40]
        })
        self.group_df = pd.DataFrame({
            "price": [100, 200, 150, 250, 300],
            "rating": [4.5, 4.7, 4.8, 4.6, 4.7],
            "review_count": [10, 15, 10, 20, 20],
            "source": ["amazon", "amazon", "mc", "mc", "mc"],
            "category": ["laptop", "laptop", "desktop", "laptop", "desktop"]
        })
        self.df_with_nulls_and_uniques = pd.DataFrame({
            "price": [1, 2, None, 4],
            "rating": [None, 5, 5, 5],
            "category": ["laptop", "laptop", "desktop", None],
            "source": ["amazon", "amazon", None, None]
        })
        self.non_numeric_df = pd.DataFrame({
            "name": ["a", "b", "c"],
            "brand": ["x", "y", "x"]
        })

    def test_summary_empty(self):
        se = StatisticsEngine(pd.DataFrame())
        self.assertEqual(se.summary(), {})

    def test_summary_numeric(self):
        se = StatisticsEngine(self.minimal_numeric_df)
        result = se.summary()
        self.assertIn("price", result)
        self.assertAlmostEqual(result["price"]["median"], 2.5)
        self.assertIn("rating", result)
        self.assertIn("review_count", result)

    def test_null_summary(self):
        se = StatisticsEngine(self.df_with_nulls_and_uniques)
        nulls = se.null_summary()
        self.assertEqual(nulls, {
            "price": 1,
            "rating": 1,
            "category": 1,
            "source": 2
        })

    def test_unique_counts(self):
        se = StatisticsEngine(self.df_with_nulls_and_uniques)
        uniques = se.unique_counts()
        self.assertEqual(uniques, {
            "price": 3,
            "rating": 1,
            "category": 2,
            "source": 1
        })

    def test_by_source_grouping(self):
        se = StatisticsEngine(self.group_df)
        stats = se.by_source()
        self.assertIn("price", stats)
        price_keys = stats["price"].keys()
        self.assertIn(('count', 'amazon'), price_keys)
        self.assertIn(('count', 'mc'), price_keys)

    def test_by_category_grouping(self):
        se = StatisticsEngine(self.group_df)
        stats = se.by_category()
        self.assertIn("price", stats)
        price_keys = stats["price"].keys()
        self.assertIn(('count', 'laptop'), price_keys)
        self.assertIn(('count', 'desktop'), price_keys)

    def test_overall_report_covers_all(self):
        df = self.minimal_numeric_df.copy()
        df["source"] = ["a", "a", "b", "b"]
        df["category"] = ["c1", "c1", "c2", "c2"]
        se = StatisticsEngine(df)
        report = se.overall_report()
        self.assertSetEqual(set(report.keys()), {"summary", "nulls", "uniques", "by_source", "by_category"})
        self.assertIsInstance(report["summary"], dict)
        self.assertIsInstance(report["nulls"], dict)
        self.assertIsInstance(report["uniques"], dict)
        self.assertIsInstance(report["by_source"], dict)
        self.assertIsInstance(report["by_category"], dict)

    def test_summary_non_numeric(self):
        se = StatisticsEngine(self.non_numeric_df)
        s = se.summary()
        self.assertIn("name", s)
        self.assertIn("brand", s)

    def test_grouping_when_column_missing(self):
        se = StatisticsEngine(self.minimal_numeric_df)
        self.assertEqual(se.by_source(), {})
        self.assertEqual(se.by_category(), {})


if __name__ == "__main__":
    unittest.main()

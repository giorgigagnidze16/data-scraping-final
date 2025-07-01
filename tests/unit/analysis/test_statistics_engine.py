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
        self.assertEqual(result["review_count"]["sum"], 100)

    def test_null_summary(self):
        se = StatisticsEngine(self.df_with_nulls_and_uniques)
        nulls = se.null_summary()
        # Only columns in BUSINESS_FIELDS are counted
        expected = {
            "price": 1,
            "rating": 1,
            "category": 1,
            "source": 2
        }
        for k in expected:
            self.assertEqual(nulls[k], expected[k])

    def test_unique_counts(self):
        se = StatisticsEngine(self.df_with_nulls_and_uniques)
        uniques = se.unique_counts()
        self.assertIn("category", uniques)
        self.assertIn("source", uniques)

    def test_by_source_grouping(self):
        se = StatisticsEngine(self.group_df)
        stats = se.by_source()
        self.assertIn("price", stats)
        for tup in stats["price"].keys():
            self.assertIsInstance(tup, tuple)

    def test_by_category_grouping(self):
        se = StatisticsEngine(self.group_df)
        stats = se.by_category()
        self.assertIn("price", stats)
        for tup in stats["price"].keys():
            self.assertIsInstance(tup, tuple)

    def test_by_source_missing(self):
        # Should raise KeyError if 'source' not in DataFrame
        se = StatisticsEngine(self.minimal_numeric_df)
        with self.assertRaises(KeyError):
            se.by_source()

    def test_by_category_missing(self):
        # Should raise KeyError if 'category' not in DataFrame
        se = StatisticsEngine(self.minimal_numeric_df)
        with self.assertRaises(KeyError):
            se.by_category()

if __name__ == "__main__":
    unittest.main()

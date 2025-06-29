import unittest

import pandas as pd

from src.analysis.comparative import ComparativeAnalyzer


class TestComparativeAnalyzer(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "category": ["laptop", "laptop", "desktop", "desktop", "tablet", "tablet", "phone"],
            "source": ["amazon", "mc", "amazon", "mc", "amazon", "mc", "amazon"],
            "price": [1000, 1100, 900, 950, 500, 550, 600],
            "rating": [4.5, 4.6, 4.3, 4.4, 4.8, 4.7, 4.9],
            "review_count": [100, 200, 150, 100, 80, 70, 300],
            "title": ["A", "B", "C", "D", "E", "F", "G"]
        })

    def test_basic_mutual_categories(self):
        result = ComparativeAnalyzer.mutual_category_comparison(self.df)
        self.assertTrue((result['category'] != 'phone').all())
        self.assertEqual(len(result), 6)
        for col in [
            'category', 'source', 'avg_price', 'median_price', 'min_price', 'max_price',
            'avg_rating', 'median_rating', 'min_rating', 'max_rating',
            'avg_review_count', 'median_review_count', 'min_review_count', 'max_review_count',
            'count'
        ]:
            self.assertIn(col, result.columns)
        row = result[(result['category'] == 'laptop') & (result['source'] == 'amazon')]
        self.assertAlmostEqual(row['avg_price'].iloc[0], 1000)
        self.assertEqual(row['count'].iloc[0], 1)

    def test_no_mutual_categories(self):
        df = pd.DataFrame({
            "category": ["laptop", "desktop", "tablet"],
            "source": ["amazon", "mc", "other"],
            "price": [1, 2, 3],
            "rating": [4, 5, 6],
            "review_count": [10, 20, 30],
            "title": ["A", "B", "C"]
        })
        result = ComparativeAnalyzer.mutual_category_comparison(df, min_sources=2)
        self.assertTrue(result.empty)

    def test_min_sources_greater_than_2(self):
        df = pd.DataFrame({
            "category": ["cat1", "cat1", "cat1", "cat2", "cat2"],
            "source": ["a", "b", "c", "a", "b"],
            "price": [1, 2, 3, 4, 5],
            "rating": [5, 4, 3, 2, 1],
            "review_count": [10, 20, 30, 40, 50],
            "title": ["A", "B", "C", "D", "E"]
        })
        result = ComparativeAnalyzer.mutual_category_comparison(df, min_sources=3)
        self.assertTrue((result['category'] == "cat1").all())
        self.assertEqual(result['category'].nunique(), 1)
        self.assertEqual(result['source'].nunique(), 3)

    def test_custom_features(self):
        result = ComparativeAnalyzer.mutual_category_comparison(self.df, features=['price'])
        expected_cols = ['category', 'source', 'avg_price', 'median_price', 'min_price', 'max_price', 'count']
        self.assertTrue(set(expected_cols).issubset(result.columns))

    def test_missing_feature_column(self):
        df = self.df.drop('rating', axis=1)
        with self.assertRaises(KeyError):
            ComparativeAnalyzer.mutual_category_comparison(df, features=['rating'])


if __name__ == "__main__":
    unittest.main()

import unittest

import pandas as pd

from src.analysis.trends import TrendAnalyzer


class TestTrendAnalyzer(unittest.TestCase):
    def setUp(self):
        self.df_complete = pd.DataFrame({
            'category': ['laptop', 'laptop', 'desktop', 'desktop'],
            'source': ['amazon', 'mc', 'amazon', 'mc'],
            'price': [1000, 1100, 900, 950],
            'review_count': [100, 200, 150, 50]
        })
        self.df_missing_price = pd.DataFrame({
            'category': ['laptop'],
            'source': ['amazon'],
            'review_count': [50]
        })
        self.df_missing_review = pd.DataFrame({
            'category': ['laptop'],
            'source': ['amazon'],
            'price': [1000]
        })

    def test_price_trend_over_categories_normal(self):
        ta = TrendAnalyzer(self.df_complete)
        result = ta.price_trend_over_categories()
        self.assertEqual(len(result), 4)
        self.assertIn('category', result.columns)
        self.assertIn('source', result.columns)
        self.assertIn('price', result.columns)
        row = result[(result['category'] == 'laptop') & (result['source'] == 'amazon')]
        self.assertAlmostEqual(row['price'].iloc[0], 1000)

    def test_review_trend_normal(self):
        ta = TrendAnalyzer(self.df_complete)
        result = ta.review_trend()
        self.assertEqual(len(result), 4)
        self.assertIn('category', result.columns)
        self.assertIn('source', result.columns)
        self.assertIn('review_count', result.columns)
        row = result[(result['category'] == 'desktop') & (result['source'] == 'amazon')]
        self.assertAlmostEqual(row['review_count'].iloc[0], 150)

    def test_price_trend_missing_column(self):
        ta = TrendAnalyzer(self.df_missing_price)
        result = ta.price_trend_over_categories()
        self.assertTrue(result.empty)
        self.assertIsInstance(result, pd.DataFrame)

    def test_review_trend_missing_column(self):
        ta = TrendAnalyzer(self.df_missing_review)
        result = ta.review_trend()
        self.assertTrue(result.empty)
        self.assertIsInstance(result, pd.DataFrame)

    def test_price_trend_partial_missing(self):
        df = pd.DataFrame({
            'source': ['amazon'],
            'price': [123]
        })
        ta = TrendAnalyzer(df)
        result = ta.price_trend_over_categories()
        self.assertTrue(result.empty)

    def test_review_trend_partial_missing(self):
        df = pd.DataFrame({
            'category': ['desktop'],
            'review_count': [12]
        })
        ta = TrendAnalyzer(df)
        result = ta.review_trend()
        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()

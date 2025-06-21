import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("trends")


class TrendAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def price_trend_over_categories(self):
        required_cols = {'category', 'source', 'price'}
        if not required_cols.issubset(self.df.columns):
            logger.warn(f"Missing columns for price trend: {required_cols - set(self.df.columns)}")
            return pd.DataFrame()

        trend = self.df.groupby(['category', 'source'])['price'].mean().reset_index()
        return trend

    def review_trend(self):
        required_cols = {'category', 'source', 'review_count'}
        if not required_cols.issubset(self.df.columns):
            logger.warn(f"Missing columns for review trend: {required_cols - set(self.df.columns)}")
            return pd.DataFrame()

        return self.df.groupby(['category', 'source'])['review_count'].mean().reset_index()

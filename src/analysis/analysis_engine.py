from collections import Counter

import numpy as np
import pandas as pd

from src.analysis.reports import ReportGenerator
from src.analysis.statistics import StatisticsEngine
from src.analysis.trends import TrendAnalyzer


class AnalysisEngine:
    """
    Orchestrates all analysis modules for scraped data.
    Applies feature engineering, runs statistics and trend analysis, and generates reports.

    Usage:
        engine = AnalysisEngine(df)
        engine.export_all("data_output")
    """

    def __init__(self, df):
        self.df = df.copy()
        self.feature_engineering()
        self.stats_engine = StatisticsEngine(self.df)
        self.trend_engine = TrendAnalyzer(self.df)
        self._summary = self.stats_engine.summary()
        self._by_source = self.stats_engine.by_source()
        self._by_category = self.stats_engine.by_category()
        self._nulls = self.stats_engine.null_summary()
        self._uniques = self.stats_engine.unique_counts()
        self._price_trend = self.trend_engine.price_trend_over_categories()
        self._review_trend = self.trend_engine.review_trend()

    def summary_statistics(self):
        """
        Returns the overall summary statistics of the data.

        Returns:
            dict: Descriptive statistics for all numeric columns.
        """
        return self._summary

    def nulls(self):
        """
        Returns the number of null/missing values per column.

        Returns:
            dict: Null count per column.
        """
        return self._nulls

    def uniques(self):
        """
        Returns the count of unique values per column.

        Returns:
            dict: Unique count per column.
        """
        return self._uniques

    def by_source(self):
        """
        Returns grouped statistics by data source.

        Returns:
            dict: Descriptive statistics grouped by source.
        """
        return self._by_source

    def by_category(self):
        """
        Returns grouped statistics by category.

        Returns:
            dict: Descriptive statistics grouped by category.
        """
        return self._by_category

    def trend_analysis(self):
        """
        Returns trend analyses such as price and review trends.

        Returns:
            dict: Trend dataframes.
        """
        return {
            "price_trend": self._price_trend,
            "review_trend": self._review_trend
        }

    def overall_report(self):
        """
        Returns a dictionary combining all key analyses.

        Returns:
            dict: Summary, nulls, uniques, group statistics, and trends.
        """
        return {
            "summary": self.summary_statistics(),
            "nulls": self.nulls(),
            "uniques": self.uniques(),
            "by_source": self.by_source(),
            "by_category": self.by_category(),
            "trends": self.trend_analysis(),
        }

    def export_all(self, data_dir="data_output"):
        """
        Exports the analysis and cleaned data to JSON and CSV, and prints report.

        Parameters:
            data_dir (str): Directory to save the outputs.
        """
        reporter = ReportGenerator(
            self.df,
            stats={
                "summary": self._summary,
                "nulls": self._nulls,
                "uniques": self._uniques,
                "by_source": self._by_source,
                "by_category": self._by_category,
            },
            trends={
                "price_trend": self._price_trend,
                "review_trend": self._review_trend,
            }
        )
        reporter.to_json(f"{data_dir}/full_report.json")
        reporter.to_csv(f"{data_dir}/products_clean_report.csv")
        reporter.print_report()

    def feature_engineering(self):
        """
        Applies feature engineering to the dataframe, including outlier detection,
        price group flags, and quantile calculations.

        Returns:
            self: The updated AnalysisEngine instance.
        """
        if not self.df.empty:
            median = self.df['price'].median()
            self.df['expensive'] = self.df['price'] > median

            quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]
            price_quantiles = self.df['price'].quantile(quantiles)
            for q, value in price_quantiles.items():
                self.df[f'price_q_{int(q * 100)}'] = self.df['price'] > value

            n_bins = min(4, len(self.df['price'].unique()))
            if n_bins > 1:
                self.df['price_group'] = pd.qcut(self.df['price'], q=n_bins,
                                                 labels=['Low', 'Mid-Low', 'Mid-High', 'High'][:n_bins])
            else:
                self.df['price_group'] = 'Low'
            self.df['price_flag'] = np.where(self.df['price'] < 50, 'very_low',
                                             np.where(self.df['price'] > 5000, 'very_high', 'normal'))

            q1 = self.df['price'].quantile(0.25)
            q3 = self.df['price'].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            self.df['outlier'] = (self.df['price'] < lower) | (self.df['price'] > upper)
        return self

    def comparative_analysis(
            self,
            features=('price', 'rating', 'review_count'),
            min_sources=2
    ):
        """
        Returns a DataFrame comparing each mutual category across sources
        for the specified features.

        Parameters:
            features (tuple): Features to compare.
            min_sources (int): Minimum number of sources for a category to be considered mutual.

        Returns:
            pd.DataFrame: Aggregated comparison statistics.
        """
        df = self.df
        categories_per_source = df.groupby('source')['category'].unique().to_dict()
        all_cats = sum([list(cats) for cats in categories_per_source.values()], [])
        mutual_cats = [cat for cat, count in Counter(all_cats).items() if count >= min_sources]
        df_mutual = df[df['category'].isin(mutual_cats)]

        agg_dict = {}
        for feat in features:
            agg_dict[f'avg_{feat}'] = (feat, 'mean')
            agg_dict[f'median_{feat}'] = (feat, 'median')
            agg_dict[f'min_{feat}'] = (feat, 'min')
            agg_dict[f'max_{feat}'] = (feat, 'max')
        agg_dict['count'] = ('title', 'count')

        comparison = (
            df_mutual
            .groupby(['category', 'source'])
            .agg(**agg_dict)
            .reset_index()
        )
        return comparison

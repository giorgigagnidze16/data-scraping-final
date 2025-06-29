import pandas as pd


class StatisticsEngine:
    """
    Performs statistical analysis and generates descriptive statistics
    for the dataset, including by group (source/category).
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def summary(self):
        """
        Generate summary descriptive statistics for all columns.

        Returns:
            dict: Statistical summary.
        """
        if self.df.empty or len(self.df.columns) == 0:
            return {}

        summary = self.df.describe(
            include='all',
            percentiles=[0.25, 0.5, 0.75]
        ).to_dict()

        for col in self.df.select_dtypes(include='number').columns:
            if col in summary:
                summary[col]["median"] = float(self.df[col].median())

        return summary

    def by_source(self):
        """
        Generate statistics grouped by 'source'.

        Returns:
            dict: Grouped statistics for each numeric column by source.
        """
        group_stats = {}
        if "source" in self.df.columns:
            group = self.df.groupby('source')
            for field in ["price", "rating", "review_count"]:
                if field in self.df.columns:
                    desc = group[field].describe(percentiles=[0.25, 0.5, 0.75]).unstack().to_dict()
                    med = group[field].median().to_dict()
                    for key in desc:
                        if isinstance(desc[key], dict):
                            desc[key]['median'] = float(med.get(key, float('nan')))
                    group_stats[field] = desc
        return group_stats

    def by_category(self):
        """
        Generate statistics grouped by 'category'.

        Returns:
            dict: Grouped statistics for each numeric column by category.
        """
        group_stats = {}
        if "category" in self.df.columns:
            group = self.df.groupby('category')
            for field in ["price", "rating", "review_count"]:
                if field in self.df.columns:
                    desc = group[field].describe(percentiles=[0.25, 0.5, 0.75]).unstack().to_dict()
                    med = group[field].median().to_dict()
                    for key in desc:
                        if isinstance(desc[key], dict):
                            desc[key]['median'] = float(med.get(key, float('nan')))
                    group_stats[field] = desc
        return group_stats

    def null_summary(self):
        """
        Count null/missing values per column.

        Returns:
            dict: Null count per column.
        """
        return self.df.isnull().sum().to_dict()

    def unique_counts(self):
        """
        Count unique values per column.

        Returns:
            dict: Unique value counts per column.
        """
        return {col: self.df[col].nunique() for col in self.df.columns}

    def overall_report(self):
        """
        Generate a full report with all statistics.

        Returns:
            dict: Combined report.
        """
        return {
            "summary": self.summary(),
            "nulls": self.null_summary(),
            "uniques": self.unique_counts(),
            "by_source": self.by_source(),
            "by_category": self.by_category(),
        }

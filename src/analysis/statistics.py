import pandas as pd


class StatisticsEngine:
    """
    Business-focused stats for product analytics.
    Only analyzes business-relevant fields, treating negative review_count/rating as missing.
    """
    NUMERIC_FIELDS = ['price', 'rating', 'review_count']
    CATEGORICAL_FIELDS = ['category', 'source']

    def __init__(self, df):
        self.df = df.copy()

    def _clean_for_stats(self, df):
        df_clean = df.copy()
        for col in ['rating', 'review_count']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].where(df_clean[col] >= 0, pd.NA)
        return df_clean

    def summary(self):
        fields = [f for f in self.NUMERIC_FIELDS if f in self.df.columns]
        if not fields:
            return {}
        df_clean = self._clean_for_stats(self.df)
        summary = df_clean[fields].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
        for col in fields:
            summary[col]["median"] = float(df_clean[col].median())
            total = float(df_clean[col].sum(skipna=True))
            summary[col]["sum"] = total
            if col == "review_count":
                summary[col]["count"] = total
        return summary

    def _safe_group_stats(self, groupby_col):
        df_clean = self._clean_for_stats(self.df)
        group_stats = {}
        for field in self.NUMERIC_FIELDS:
            if field in df_clean.columns:
                group = df_clean.groupby(groupby_col)[field]
                desc = group.describe(percentiles=[0.25, 0.5, 0.75]).unstack().to_dict()
                med = group.median().to_dict()
                for k in desc:
                    val = desc[k]
                    if isinstance(val, dict):
                        val['median'] = float(med.get(k, float('nan')))
                        desc[k] = val
                    else:
                        desc[k] = {'value': float(val), 'median': float(med.get(k, float('nan')))}
                group_stats[field] = desc
        return group_stats

    def by_category(self):
        return self._safe_group_stats('category')

    def by_source(self):
        return self._safe_group_stats('source')

    def null_summary(self):
        BUSINESS_FIELDS = [
            "id", "source", "category", "title", "price",
            "rating", "review_count", "url", "img_url", "scraped_at"
        ]
        df_clean = self._clean_for_stats(self.df)
        all_nulls = df_clean.isnull().sum().to_dict()
        business_nulls = {col: all_nulls[col] for col in BUSINESS_FIELDS if col in all_nulls}
        return business_nulls

    def unique_counts(self):
        """
        Only count uniques for relevant categorical columns.
        """
        fields = self.CATEGORICAL_FIELDS
        fields = [f for f in fields if f in self.df.columns]
        return {col: self.df[col].nunique() for col in fields}

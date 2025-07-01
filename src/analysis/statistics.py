class StatisticsEngine:
    """
    Business-focused stats for product analytics.
    Only analyzes business-relevant fields.
    """

    NUMERIC_FIELDS = ['price', 'rating', 'review_count']
    CATEGORICAL_FIELDS = ['category', 'source']

    def __init__(self, df):
        self.df = df.copy()

    def summary(self):
        """
        Only get describe() for relevant numeric columns.
        """
        fields = [f for f in self.NUMERIC_FIELDS if f in self.df.columns]
        if not fields:
            return {}

        summary = self.df[fields].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
        # Add median explicitly if you like
        for col in fields:
            summary[col]["median"] = float(self.df[col].median())
        return summary

    def by_source(self):
        group_stats = {}
        for field in self.NUMERIC_FIELDS:
            if field in self.df.columns:
                group = self.df.groupby('source')[field]
                desc = group.describe(percentiles=[0.25, 0.5, 0.75]).unstack().to_dict()
                med = group.median().to_dict()
                for k in desc:
                    if isinstance(desc[k], dict):
                        desc[k]['median'] = float(med.get(k, float('nan')))
                group_stats[field] = desc
        return group_stats

    def by_category(self):
        group_stats = {}
        for field in self.NUMERIC_FIELDS:
            if field in self.df.columns:
                group = self.df.groupby('category')[field]
                desc = group.describe(percentiles=[0.25, 0.5, 0.75]).unstack().to_dict()
                med = group.median().to_dict()
                for k in desc:
                    if isinstance(desc[k], dict):
                        desc[k]['median'] = float(med.get(k, float('nan')))
                group_stats[field] = desc
        return group_stats

    def null_summary(self):
        """
        Only report nulls for relevant columns.
        """
        BUSINESS_FIELDS = [
            "id", "source", "category", "title", "price",
            "rating", "review_count", "url", "img_url", "scraped_at"
        ]

        all_nulls = self.df.isnull().sum().to_dict()
        business_nulls = {col: all_nulls[col] for col in BUSINESS_FIELDS if col in all_nulls}
        return business_nulls

    def unique_counts(self):
        """
        Only count uniques for relevant categorical columns.
        """
        fields = self.CATEGORICAL_FIELDS
        fields = [f for f in fields if f in self.df.columns]
        return {col: self.df[col].nunique() for col in fields}

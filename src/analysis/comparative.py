from collections import Counter

import pandas as pd


class ComparativeAnalyzer:
    """
    Provides methods to compare mutual categories across multiple sources
    for features such as price, rating, and review_count.
    """

    @staticmethod
    def mutual_category_comparison(
            df: pd.DataFrame,
            features=('price', 'rating', 'review_count'),
            min_sources=2
    ):
        """
        Compare mutual categories (present in at least `min_sources` sources) for specified features.

        Parameters:
            df (pd.DataFrame): Data for comparison.
            features (tuple): Features to compare.
            min_sources (int): Minimum sources a category must appear in to be compared.

        Returns:
            pd.DataFrame: Aggregated statistics for mutual categories.
        """
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

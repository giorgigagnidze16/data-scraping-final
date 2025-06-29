from collections import Counter

import pandas as pd


class ComparativeAnalyzer:
    @staticmethod
    def mutual_category_comparison(
            df: pd.DataFrame,
            features=('price', 'rating', 'review_count'),
            min_sources=2
    ):
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

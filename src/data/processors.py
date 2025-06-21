import pandas as pd


class ProductDataProcessor:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def clean_and_validate(self):
        self.df = self.df.dropna(subset=['title', 'price', 'url'])
        self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
        if 'rating' in self.df:
            self.df['rating'] = pd.to_numeric(self.df['rating'], errors='coerce')
        if 'review_count' in self.df:
            self.df['review_count'] = pd.to_numeric(self.df['review_count'], errors='coerce').fillna(0).astype(int)
        if 'source' in self.df:
            self.df['source'] = self.df['source'].str.lower()
        if 'category' in self.df:
            self.df['category'] = self.df['category'].str.lower()
        self.df = self.df.drop_duplicates(subset=['url'])
        self.df = self.df.reset_index(drop=True)
        return self

    def export(self, filename: str, filetype: str = "csv"):
        if filetype == "csv":
            self.df.to_csv(filename, index=False)
        elif filetype == "excel":
            self.df.to_excel(filename, index=False)
        elif filetype == "json":
            self.df.to_json(filename, orient='records', force_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported filetype: {filetype}")
        return self

    def get_data_quality_report(self) -> dict:
        total = len(self.df)
        missing_titles = self.df['title'].isnull().sum()
        missing_prices = self.df['price'].isnull().sum()
        missing_urls = self.df['url'].isnull().sum()
        missing_ratings = self.df['rating'].isnull().sum() if 'rating' in self.df else 0
        duplicate_urls = total - self.df['url'].nunique()
        price_neg = (self.df['price'] < 0).sum()
        outlier_prices = (self.df['price'] > self.df['price'].quantile(0.99)).sum()

        return {
            "total_rows": total,
            "missing_titles": missing_titles,
            "missing_prices": missing_prices,
            "missing_urls": missing_urls,
            "missing_ratings": missing_ratings,
            "duplicate_urls": duplicate_urls,
            "negative_prices": price_neg,
            "outlier_prices": outlier_prices
        }

    def get_df(self):
        return self.df

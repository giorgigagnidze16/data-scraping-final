import pandas as pd


class ProductDataProcessor:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def clean_and_validate(self):
        """
        Cleans the product data:

            - Drops rows missing 'title', 'price', or 'url'.
            - Converts 'price', 'rating', and 'review_count' columns to numeric types.
            - Fills missing 'review_count' with zero.
            - Converts 'source' and 'category' to lowercase (if present).
            - Removes duplicate URLs.
            - Resets the DataFrame index.

        Returns:
            self: Allows method chaining.
        """
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
        """
        Exports the cleaned DataFrame to a file.

        Args:
            filename (str): Output file name (e.g., 'output.csv').
            filetype (str): File type: 'csv', 'excel', or 'json'. Default is 'csv'.

        Raises:
            ValueError: If filetype is not supported.

        Returns:
            self: Allows method chaining.
        """
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
        """
        Checks for common data quality issues.

        Returns:
            dict: Report with keys:
                - total_rows: number of rows in the DataFrame
                - missing_titles: number of missing titles
                - missing_prices: number of missing prices
                - missing_urls: number of missing URLs
                - missing_ratings: number of missing ratings
                - duplicate_urls: number of duplicate URLs
                - negative_prices: number of prices < 0
                - outlier_prices: number of prices above 99th percentile
        """
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
        """
        Returns the processed DataFrame.

        Returns:
            pd.DataFrame: The current DataFrame with all cleaning/processing applied.
        """
        return self.df

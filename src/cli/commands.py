import base64
import operator
import os
from io import BytesIO

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.analysis.analysis_engine import AnalysisEngine
from src.data.database import load_products, load_products_raw
from src.data.processors import ProductDataProcessor

def flatten_columns(df):
    """Flatten MultiIndex columns in a DataFrame."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip('_') for col in df.columns.values]
    return df

def summarize_grouped(df, groupby="category", fields=None, agg_funcs=None):
    """
    Returns a flat, business-friendly summary DataFrame by category or source.
    """
    fields = fields or ['price', 'rating', 'review_count']
    agg_funcs = agg_funcs or ['count', 'mean', 'min', 'max', 'median']

    grouped = df.groupby(groupby)[fields].agg(agg_funcs)
    grouped = flatten_columns(grouped)
    grouped = grouped.reset_index()
    return grouped

def show_table(df, n=10, tail=False):
    if df.empty:
        print("No data found.")
        return
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 160)
    if tail:
        print(df.tail(n).to_string(index=False))
    else:
        print(df.head(n).to_string(index=False))

def show_raw_products(n=10, tail=False):
    df = load_products_raw()
    show_table(df, n=n, tail=tail)

def show_clean_products(n=10, tail=False):
    df = load_products()
    show_table(df, n=n, tail=tail)

def show_stats(clean=True):
    df = load_products() if clean else load_products_raw()
    fields = ['price', 'rating', 'review_count']
    df_stats = df[fields].describe().transpose()
    print(df_stats)

def show_columns(clean=True):
    df = load_products() if clean else load_products_raw()
    print("Columns:", ", ".join(df.columns))

def filter_products(column, op_str, value, clean=True, n=20, return_df=False):
    df = load_products() if clean else load_products_raw()
    if column not in df.columns:
        print(f"Column '{column}' not found.")
        return

    ops = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        'contains': lambda a, b: a.str.contains(str(b), case=False, na=False),
        'not contains': lambda a, b: ~a.str.contains(str(b), case=False, na=False),
    }

    if op_str not in ops:
        print(f"Unsupported operator '{op_str}'. Supported: {list(ops.keys())}")
        return

    if op_str == '==' and pd.api.types.is_numeric_dtype(df[column]):
        try:
            value = float(value)
            epsilon = 1e-4
            result = (df[column] - value).abs() < epsilon
        except ValueError:
            print(f"Value '{value}' could not be converted to float for numeric comparison.")
            return
    elif op_str == '!=' and pd.api.types.is_numeric_dtype(df[column]):
        try:
            value = float(value)
            epsilon = 1e-4
            result = (df[column] - value).abs() > epsilon
        except ValueError:
            print(f"Value '{value}' could not be converted to float for numeric comparison.")
            return
    elif op_str in {'>', '<', '>=', '<='}:
        try:
            value = float(value)
            result = ops[op_str](df[column], value)
        except ValueError:
            print(f"Value '{value}' could not be converted to float for numeric comparison.")
            return
    elif op_str in {'contains', 'not contains'}:
        result = ops[op_str](df[column].astype(str), value)
    else:
        result = ops[op_str](df[column], value)

    filtered = df[result]
    if filtered.empty:
        print("No results found.")
        return None if return_df else None
    else:
        show_table(filtered, n=min(n, len(filtered)))
        if return_df:
            return filtered
        else:
            return None

def filter_price(min_price=None, max_price=None, clean=True):
    df = load_products() if clean else load_products_raw()
    if min_price is not None:
        df = df[df['price'] >= float(min_price)]
    if max_price is not None:
        df = df[df['price'] <= float(max_price)]
    show_table(df, n=min(20, len(df)))

def export_products(file, filetype="csv", clean=True, **filters):
    df = load_products() if clean else load_products_raw()
    for col, val in filters.items():
        if col in df.columns and val:
            df = df[df[col] == val]
    if filetype == "csv":
        df.to_csv(file, index=False)
    elif filetype == "json":
        df.to_json(file, orient='records', force_ascii=False, indent=2)
    elif filetype in ("xlsx", "excel"):
        df.to_excel(file, index=False)
    else:
        print("Unsupported export type.")
        return
    print(f"Exported {len(df)} rows to {file}")

def data_quality_report(clean=True):
    df = load_products() if clean else load_products_raw()
    processor = ProductDataProcessor(df)
    processor.clean_and_validate()
    report = processor.get_data_quality_report()
    print("=== Data Quality Report ===")
    for k, v in report.items():
        print(f"{k:20}: {v}")

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def show_statistical_summary(clean=True):
    df = load_products() if clean else load_products_raw()
    fields = ['price', 'rating', 'review_count']
    df_stats = df[fields].describe().transpose()
    print("\n=== Statistical Summary ===")
    print(df_stats)

def clean_missing_values(df):
    df = df.copy()
    for col in ['rating', 'review_count']:
        df[col] = df[col].replace(-1, pd.NA)
    return df

def show_grouped_summary(by="category", clean=True):
    df = load_products() if clean else load_products_raw()
    df_stats = summarize_grouped(clean_missing_values(df), groupby=by)
    print(f"=== Summary by {by.capitalize()} ===")
    print(df_stats)

def plot_distribution(column="price", clean=True):
    df = load_products() if clean else load_products_raw()
    if column not in df.columns:
        print(f"Column '{column}' not found.")
        return
    plt.figure(figsize=(7, 4))
    sns.histplot(df[column].dropna(), bins=40, kde=True)
    plt.title(f"{column.capitalize()} Distribution")
    plt.xlabel(column.capitalize())
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()

def show_trends(clean=True):
    df = load_products() if clean else load_products_raw()
    engine = AnalysisEngine(df)
    trends = engine.trend_analysis()
    pt = trends.get('price_trend')
    if isinstance(pt, pd.DataFrame) and not pt.empty:
        plt.figure(figsize=(8, 4))
        sns.lineplot(
            data=pt,
            x='category', y='price', hue='source', marker="o"
        )
        plt.title("Average Price by Category & Source")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.show()
    rt = trends.get('review_trend')
    if isinstance(rt, pd.DataFrame) and not rt.empty:
        plt.figure(figsize=(8, 4))
        sns.lineplot(
            data=rt,
            x='category', y='review_count', hue='source', marker="o"
        )
        plt.title("Average Review Count by Category & Source")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.show()

def show_comparative_analysis(
        clean=True, features=None, min_sources=2, top_n_categories=7, plot=True
):
    """
    Advanced comparative analysis: clear grouped barplots of mean values.
    """
    df = load_products() if clean else load_products_raw()
    engine = AnalysisEngine(df)
    features = features or ('price', 'rating', 'review_count')
    comp = engine.comparative_analysis(features=features, min_sources=min_sources)

    top_categories = (
        comp.groupby('category')['count'].sum().sort_values(ascending=False)
        .head(top_n_categories).index
    )
    comp = comp[comp['category'].isin(top_categories)]

    print("\n=== Comparative Analysis ===")
    print(comp.head(top_n_categories * 3).to_string(index=False))

    if not plot:
        return

    for feat in features:
        if feat in df.columns and df['category'].nunique() <= 10:
            plt.figure(figsize=(10, 5))
            sns.stripplot(
                data=df[df['category'].isin(top_categories)],
                x="category", y=feat, hue="source", dodge=True, alpha=0.5, size=4
            )
            plt.title(f"{feat.capitalize()} Distribution by Category & Source")
            plt.xlabel("Category")
            plt.ylabel(feat.capitalize())
            plt.xticks(rotation=20)
            plt.legend(title="Source")
            plt.tight_layout()
            plt.show()

def format_floats_for_html(df, float_format="{:,.2f}"):
    """
    Convert all float columns in a DataFrame to formatted strings, e.g., 1,234.56.
    """
    for col in df.select_dtypes(include="float"):
        df[col] = df[col].apply(lambda x: float_format.format(x) if pd.notnull(x) else "")
    return df

def pretty_number(val):
    if isinstance(val, float):
        return "{:,.2f}".format(val)
    return f"{val:,}" if isinstance(val, int) else str(val)

def generate_html_report(outfile="data_output/report.html", clean=True):
    df = load_products() if clean else load_products_raw()
    analysis = AnalysisEngine(df)
    stats = analysis.summary_statistics()
    nulls = analysis.nulls()
    uniques = analysis.uniques()
    trends = analysis.trend_analysis()
    comparative = analysis.comparative_analysis(features=['price', 'rating', 'review_count'])

    def shorten_url(u, max_len=60):
        if isinstance(u, str) and len(u) > max_len:
            return f'<a href="{u}" target="_blank" rel="noopener" class="url-link">{u[:max_len]}...</a>'
        elif isinstance(u, str):
            return f'<a href="{u}" target="_blank" rel="noopener" class="url-link">{u}</a>'
        return u

    sample_df = df.head(20).copy()
    if 'url' in sample_df.columns:
        sample_df['url'] = sample_df['url'].apply(shorten_url)

    html = """
    <html>
    <head>
        <title>Product Data Report</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f6f7fa; font-family: 'Segoe UI', Arial, sans-serif; color: #222; margin: 0; font-size: 17px;}
            .container { margin: 40px auto; max-width: 1050px; background: #fff; border-radius: 10px; padding: 28px 16px 24px 16px; box-shadow: 0 2px 8px 0 #ececec33;}
            h1 { font-size: 2rem; font-weight: 600; color: #23233b; margin-bottom: 22px;}
            h2 { font-size: 1.15rem; font-weight: 500; margin: 2.3rem 0 1rem 0; color: #3a3a4f;}
            .stat-title { font-size: 1.09em; background: #f3f4f7; color: #555; padding: 0.55rem 1rem; border-radius: 6px; margin-bottom: 1.1rem; border-left: 3px solid #ececff; margin-top: 2rem;}
            .table-responsive { margin-bottom: 1.1rem; border-radius: 8px; overflow-x: auto;}
            .table { background: #fff; border-radius: 7px; overflow: hidden; border: 1px solid #e5e8f0; font-size: 0.97rem;}
            th { background: #f6f8fa !important; color: #333 !important; font-weight: 600 !important; border-bottom: 2px solid #e2e4ea !important;}
            td, th { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px; font-size: 0.97rem; border: 1px solid #e9e9ef;}
            a.url-link { color: #316ad3; text-decoration: underline dotted; font-size: 0.96em; word-break: break-all;}
            .img-fluid { border-radius: 10px; margin-top: 8px; margin-bottom: 12px;}
            @media (max-width: 700px) { .container { padding: 4px 2px; } th, td { max-width: 85px; font-size: 12px;} h1 { font-size: 1.2rem;} h2 { font-size: 1.01rem;} .stat-title { padding: 0.35rem 0.7rem;}}
        </style>
    </head>
    <body>
    <div class="container">
    <h1>Product Data Report</h1>
    """

    review_col = 'review_count' if 'review_count' in df.columns else None
    if review_col:
        reviews = df[review_col].where(df[review_col] >= 0, pd.NA)
        total_reviews = int(reviews.sum(skipna=True))
        product_count = len(df)
        products_with_reviews = int((reviews > 0).sum())
        html += '<div class="stat-title"><h2>Business Summary</h2></div>'
        html += f'<ul>'
        html += f'<li><b>Total Products:</b> {pretty_number(product_count)}</li>'
        html += f'<li><b>Total Reviews:</b> {pretty_number(total_reviews)}</li>'
        html += f'<li><b>Products With Reviews:</b> {pretty_number(products_with_reviews)}</li>'
        html += f'</ul>'

    if stats:
        stats_df = pd.DataFrame(stats)
        stats_df = flatten_columns(stats_df)
        stats_df = stats_df.reset_index()
        stats_df = format_floats_for_html(stats_df)
        html += '<div class="stat-title"><h2>Summary Statistics</h2></div>'
        html += '<div class="table-responsive">'
        html += stats_df.to_html(classes="table table-striped table-bordered", border=0, index=False)
        html += '</div>'
    if nulls:
        html += '<div class="stat-title"><h2>Missing Values</h2></div>'
        html += '<div class="table-responsive">'
        html += pd.DataFrame(list(nulls.items()), columns=['Column', 'Missing']).to_html(
            classes="table table-hover table-bordered", index=False, border=0)
        html += '</div>'
    if trends:
        trend_labels = {
            "price_trend": "Price Trend",
            "review_trend": "Review Count Trend"
        }
        for key, label in trend_labels.items():
            trend_df = trends.get(key)
            if isinstance(trend_df, pd.DataFrame) and not trend_df.empty:
                fig, ax = plt.subplots(figsize=(8, 4))
                ycol = "price" if "price" in trend_df.columns else "review_count"
                sns.lineplot(data=trend_df, x="category", y=ycol, hue="source", marker="o", ax=ax)
                ax.set_title(f"{label} by Category & Source")
                plt.xticks(rotation=25)
                html += f'<div class="stat-title"><h2>{label} by Category & Source</h2></div>'
                img_base64 = fig_to_base64(fig)
                html += f'<img src="data:image/png;base64,{img_base64}" class="img-fluid mb-4" style="max-width:650px;"><br>'
    if uniques:
        html += '<div class="stat-title"><h2>Unique Values</h2></div>'
        html += '<div class="table-responsive">'
        html += pd.DataFrame(list(uniques.items()), columns=['Column', 'Unique Count']).to_html(
            classes="table table-hover table-bordered", index=False, border=0)
        html += '</div>'
    html += '''
    <div class="stat-title"><h2>Sample Data</h2></div>
    <div class="table-responsive">
        <table class="table table-sm table-bordered align-middle" style="table-layout:fixed; word-break:break-all;">
            <thead class="table-light">
                <tr>''' + ''.join([f"<th style='max-width:150px'>{col}</th>" for col in sample_df.columns]) + '''</tr>
            </thead>
            <tbody>
    '''
    for _, row in sample_df.iterrows():
        html += "<tr>" + "".join(
            [f"<td style='max-width:150px; overflow-x:auto;'>{cell if not pd.isnull(cell) else ''}</td>" for cell in
             row]
        ) + "</tr>"
    html += '''
            </tbody>
        </table>
    </div>
    '''

    if 'price' in df.columns and df['price'].notnull().any():
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(df['price'].dropna(), bins=40, kde=True, ax=ax)
        ax.set_title("Price Distribution")
        ax.set_xlabel("Price")
        ax.set_ylabel("Count")
        html += '<div class="stat-title"><h2>Price Distribution</h2></div>'
        img_base64 = fig_to_base64(fig)
        html += f'<img src="data:image/png;base64,{img_base64}" class="img-fluid mb-4" style="max-width:650px;"><br>'

    if isinstance(comparative, pd.DataFrame) and not comparative.empty:
        feature_labels = {
            "price": "Price", "rating": "Rating", "review_count": "Review Count"
        }
        for feat in ["price", "rating", "review_count"]:
            col = f'avg_{feat}'
            if col in comparative.columns:
                fig, ax = plt.subplots(figsize=(8, 4))
                sns.barplot(data=comparative, x="category", y=col, hue="source", ax=ax)
                ax.set_title(f"Avg {feature_labels.get(feat, feat.capitalize())} by Category & Source")
                ax.set_xlabel("Category")
                ax.set_ylabel(f"Avg {feature_labels.get(feat, feat.capitalize())}")
                plt.xticks(rotation=25)
                html += f'<div class="stat-title"><h2>Comparative Analysis: Avg {feature_labels.get(feat, feat.capitalize())} by Category & Source</h2></div>'
                img_base64 = fig_to_base64(fig)
                html += f'<img src="data:image/png;base64,{img_base64}" class="img-fluid mb-4" style="max-width:650px;"><br>'

        html += '<div class="stat-title"><h2>Comparative Stats Table</h2></div>'
        html += '<div class="table-responsive">'
        html += comparative.to_html(classes="table table-striped table-bordered", index=False)
        html += '</div>'

        for feat in ["price", "rating", "review_count"]:
            if feat in df.columns and df['category'].nunique() < 20:
                fig, ax = plt.subplots(figsize=(10, 4))
                sns.boxplot(
                    data=df[df['category'].isin(comparative['category'].unique())],
                    x="category", y=feat, hue="source", ax=ax
                )
                ax.set_title(f"{feature_labels.get(feat, feat.capitalize())} Distribution by Category & Source")
                plt.xticks(rotation=25)
                img_base64 = fig_to_base64(fig)
                html += f'<div class="stat-title"><h2>{feature_labels.get(feat, feat.capitalize())} Distribution Boxplot</h2></div>'
                html += f'<img src="data:image/png;base64,{img_base64}" class="img-fluid mb-4" style="max-width:650px;"><br>'

    html += """
    </div>
    </body>
    </html>
    """
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report written to {outfile}")

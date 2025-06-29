import pytest

@pytest.fixture
def sample_microcenter_product_html():
    return """
    <html>
        <body>
            <ul>
                <li class='product_wrapper'>
                    <div class='h2'><a href='/product/12345'>Sample Product</a></div>
                    <div class='image2'><img src='https://image.com/product.jpg' /></div>
                    <div class='price_wrapper'>
                        <div class='price'><span itemprop='price'>$999.99</span></div>
                    </div>
                </li>
            </ul>
        </body>
    </html>
    """

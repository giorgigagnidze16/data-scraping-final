import pytest

@pytest.fixture
def sample_amazon_product_html():
    return """
    <html>
        <body>
            <div data-component-type='s-search-result'>
                <div class='sg-col-inner'>
                    <h2><span>Test Product</span></h2>
                    <h2><a href='/dp/B000000'>Link</a></h2>
                    <img class='s-image' src='img.jpg'/>
                    <span class='a-price-whole'>123</span>
                    <span class='a-price-fraction'>99</span>
                </div>
            </div>
        </body>
    </html>
    """

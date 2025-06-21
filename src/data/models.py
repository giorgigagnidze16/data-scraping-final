from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    source: str
    category: str
    title: str
    price: float
    rating: Optional[float]
    review_count: Optional[int]
    url: str
    img_url: Optional[str]

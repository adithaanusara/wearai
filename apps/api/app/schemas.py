from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel

from app import security
from app.models import Product, Review


class CamelModel(BaseModel):
    """Python code uses snake_case; the JSON uses camelCase, matching the web app's types."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Page[T](CamelModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class ProductOut(CamelModel):
    id: str
    slug: str
    style_id: str
    name: str
    gender: str
    category: str
    colour: str
    price: int
    compare_at_price: int | None
    images: list[str]
    sizes: list[str]
    is_new: bool
    is_best_seller: bool
    description: str
    details: list[str]

    @classmethod
    def from_product(cls, product: Product) -> "ProductOut":
        return cls(
            id=product.id,
            slug=product.slug,
            style_id=product.style_id,
            name=product.name,
            gender=product.gender,
            category=product.category,
            colour=product.colour,
            price=product.price,
            compare_at_price=product.compare_at_price,
            images=[image.url for image in product.images],
            sizes=[size.label for size in product.sizes],
            is_new=product.is_new,
            is_best_seller=product.is_best_seller,
            description=product.description,
            details=[detail.text for detail in product.details],
        )


class ColourwayOut(CamelModel):
    id: str
    slug: str
    colour: str


class RatingOut(CamelModel):
    average: float | None
    count: int


class ProductDetailOut(ProductOut):
    colourways: list[ColourwayOut]
    rating: RatingOut


class ReviewOut(CamelModel):
    id: str
    style_id: str
    rating: int
    title: str
    body: str
    author: str
    date: date

    @classmethod
    def from_review(cls, review: Review) -> "ReviewOut":
        return cls(
            id=review.id,
            style_id=review.style_id,
            rating=review.rating,
            title=review.title,
            body=review.body,
            author=review.author,
            date=review.review_date,
        )


class FilterOptionsOut(CamelModel):
    sizes: list[str]
    colours: list[str]
    min_price: int
    max_price: int


class CollectionOut(Page[ProductOut]):
    slug: str
    title: str
    filter_options: FilterOptionsOut


def _clean_email(value: str) -> str:
    return value.strip().lower()


class RegisterIn(CamelModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 120:
            raise ValueError("Enter a name of up to 120 characters.")
        return value

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _clean_email(value)

    @field_validator("password")
    @classmethod
    def _password(cls, value: str) -> str:
        problem = security.password_problem(value)
        if problem:
            raise ValueError(problem)
        return value


class LoginIn(CamelModel):
    email: EmailStr
    # Only a length limit here; strength rules apply when a password is chosen.
    password: str = Field(min_length=1, max_length=security.MAX_PASSWORD_LENGTH)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _clean_email(value)


class UserOut(CamelModel):
    id: int
    name: str
    email: str

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class __Base(DeclarativeBase):
    pass


class DbModel(__Base):
    __tablename__ = "data"
    id: Mapped[int] = mapped_column(primary_key=True)
    num: Mapped[int]
    data: Mapped[str]


class DomainModel(BaseModel):
    id: int
    num: int
    data: str

    model_config = ConfigDict(from_attributes=True)

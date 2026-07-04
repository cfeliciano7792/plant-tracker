from pydantic import BaseModel


class GroupCount(BaseModel):
    label: str
    count: int


class StatsOut(BaseModel):
    total_count: int
    by_origin_region: list[GroupCount]
    by_origin_country: list[GroupCount]
    by_family: list[GroupCount]
    by_genus: list[GroupCount]

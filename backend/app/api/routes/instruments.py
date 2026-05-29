from fastapi import APIRouter
from typing import List

from app.schemas.schemas import InstrumentOut

router = APIRouter()

# Static instrument data (previously stored in SQLite via Django ORM).
# Replace with a DB query if a dynamic data source is needed.
_INSTRUMENTS = [
    {"name": "Đàn bầu", "description": "Monochord zither, one of Vietnam's most unique instruments."},
    {"name": "Đàn tranh", "description": "16-string zither derived from the Chinese guzheng."},
    {"name": "Đàn nguyệt", "description": "Moon-shaped two-string lute."},
    {"name": "Đàn tỳ bà", "description": "Pear-shaped lute with four strings."},
    {"name": "Đàn cò", "description": "Two-string fiddle similar to the Chinese erhu."},
    {"name": "Khèn", "description": "Mouth organ of the Hmong people."},
    {"name": "Cồng chiêng", "description": "Bronze gongs central to Central Highlands culture."},
    {"name": "Trống quân", "description": "Barrel drum used in folk music."},
    {"name": "Đàn đáy", "description": "Long-neck three-string lute used in ca trù."},
    {"name": "Đàn đá", "description": "Lithophone – the oldest musical instrument in Vietnam."},
    {"name": "Đàn sến", "description": "Two-string moon lute derived from the Chinese meihuaqin."},
    {"name": "Đàn tứ", "description": "Short-neck round-bodied four-string lute."},
    {"name": "Đàn t'rưng", "description": "Bamboo xylophone of the Central Highlands ethnic groups."},
    {"name": "Đàn tính", "description": "Long-neck lute of the Tày and Nùng people."},
]


@router.get("/", response_model=List[InstrumentOut])
async def list_instruments():
    """Return metadata for all supported Vietnamese traditional instruments."""
    return _INSTRUMENTS

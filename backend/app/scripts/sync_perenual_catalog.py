"""One-time bulk index of Perenual's free-tier species catalog.

Perenual's free tier only ever grants `species/details` access for ids 1-3000
(confirmed live: id 3000 works, id 3001 returns an upgrade message; species-list
pages map linearly at 30/page, so pages 1-100 cover exactly that range). This
script pages through species-list once and caches the list-level fields
(name, taxonomy, image) locally, so search never needs to call Perenual again.
Full care-info details are fetched lazily, once per species, only when a
family member actually adds it (see routers/plant_search.py).

Usage:  python -m app.scripts.sync_perenual_catalog

Spends roughly one request per page (~100 requests for the default 100 pages)
-- essentially your whole day's free quota in one run. Safe to re-run: pages
whose full id range is already indexed are skipped without spending a request,
so an interrupted run can just be re-invoked (the next day, if quota-limited).
"""

import asyncio

from sqlalchemy import select

from app.config import settings
from app.database import async_session_maker
from app.models.plant_species import PlantSpecies
from app.services.plant_providers.perenual import PerenualProvider

PAGE_SIZE = 30


async def _page_already_indexed(db, page: int) -> bool:
    first_id = (page - 1) * PAGE_SIZE + 1
    last_id = page * PAGE_SIZE
    expected_ids = {str(i) for i in range(first_id, last_id + 1)}

    result = await db.scalars(
        select(PlantSpecies.external_id).where(
            PlantSpecies.data_source == "perenual",
            PlantSpecies.external_id.in_(expected_ids),
        )
    )
    return set(result.all()) == expected_ids


async def main() -> None:
    if not settings.perenual_api_key:
        print("PERENUAL_API_KEY is not set - aborting.")
        return

    provider = PerenualProvider()
    max_page = settings.perenual_free_tier_max_page
    inserted = 0
    skipped_pages = 0

    async with async_session_maker() as db:
        for page in range(1, max_page + 1):
            if await _page_already_indexed(db, page):
                skipped_pages += 1
                continue

            try:
                items = await provider.list_page(page)
            except Exception as e:
                print(f"Page {page}: request failed ({e}). Stopping - re-run later to resume.")
                break

            if not items:
                print(f"Page {page}: empty response, stopping.")
                break

            for item in items:
                species_id = item.get("id")
                if species_id is None or not item.get("common_name"):
                    continue

                external_id = str(species_id)
                existing = await db.scalar(
                    select(PlantSpecies).where(
                        PlantSpecies.data_source == "perenual",
                        PlantSpecies.external_id == external_id,
                    )
                )
                if existing is not None:
                    continue

                fields = PerenualProvider.list_item_to_fields(item)
                db.add(
                    PlantSpecies(
                        data_source="perenual",
                        external_id=external_id,
                        details_fetched=False,
                        **fields,
                    )
                )
                inserted += 1

            await db.commit()
            print(f"Page {page}/{max_page}: indexed ({inserted} total new rows so far)")

    print(f"Done. Inserted {inserted} new species, skipped {skipped_pages} already-indexed pages.")


if __name__ == "__main__":
    asyncio.run(main())

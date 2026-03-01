from __future__ import annotations

from typing import Dict, Iterator, Optional

from app.Service.ScraperService import Scraper


class ScrappingService:
    def __init__(self) -> None:
        self._scraper = Scraper()

    def normalize_and_validate(self, base: Dict) -> Optional[Dict]:
        return self._scraper.normalize_and_validate(base)

    def stream_scrape(self, base_url: Optional[str] = None) -> Iterator[Dict]:
        yield from self._scraper.stream_scrape(base_url=base_url)

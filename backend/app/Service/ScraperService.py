import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 CarScraperBot/1.1"
    )
}

ALLOWED_BASE_URLS = {
    "https://chobrod.com/car-honda-civic/p",
    "https://chobrod.com/car-toyota-hilux-revo/p",
}


class Scraper:
    def __init__(self):
        # default (used when base_url not provided)
        self.base_url = "https://chobrod.com/car-toyota-hilux-revo/p"
        self.max_workers = 6
        self.page_delay = (0.1, 0.3)

    _YEAR_RE = re.compile(r"(20\d{2})")

    @staticmethod
    def _parse_year(title: str):
        if not title:
            return None
        m = Scraper._YEAR_RE.search(str(title))
        return m.group(1) if m else None

    @staticmethod
    def _to_int(text):
        if text is None:
            return None
        s = re.sub(r"[^\d]", "", str(text))
        return int(s) if s else None

    @staticmethod
    def _normalize_gear(gear_text: str):
        t = str(gear_text or "").lower()
        if re.search(r"อัตโนมัติ|auto|a/?t|automatic|\bat\b", t):
            return "อัตโนมัติ"
        if re.search(r"ธรรมดา|manual|m/?t|\bmt\b", t):
            return "ธรรมดา"
        return None

    @classmethod
    def _normalize_item(cls, base: dict):
        title = base.get("title")
        year = cls._parse_year(title)
        price = cls._to_int(base.get("price"))
        mile = cls._to_int(base.get("mile"))
        gear = cls._normalize_gear(base.get("gear"))
        return {
            "title": title,
            "year": year,
            "price": price,
            "gear": gear,
            "mile": mile,
            "url": base.get("url"),
        }

    @staticmethod
    def _is_complete(item: dict):
        return bool(
            item.get("title")
            and item.get("year")
            and isinstance(item.get("price"), int)
            and item.get("gear")
            and isinstance(item.get("mile"), int)
        )

    def normalize_and_validate(self, base: dict):
        item = self._normalize_item(base)
        return item if self._is_complete(item) else None

    def stream_scrape(self, base_url=None):
        # validate dropdown base_url (security + correctness)
        if base_url:
            base_url = str(base_url).strip()
            if base_url not in ALLOWED_BASE_URLS:
                raise ValueError(f"base_url not allowed: {base_url}")
            active_base = base_url
        else:
            active_base = self.base_url

        page_num = 1
        logger.info("Start streaming list from %s ...", active_base)

        while True:
            url = f"{active_base}{page_num}"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            except Exception as e:
                logger.warning("Failed to fetch list page %d: %s", page_num, e)
                break

            soup = bs(response.content, "html.parser")
            results = soup.find("div", class_="list-product")
            if not results:
                break

            title_tags = results.find_all("h2", class_="title")
            price_tags = results.find_all("p", class_="price")
            titles = [tag.find("a").text.strip() for tag in title_tags if tag.find("a")]
            prices = [tag.text.strip() for tag in price_tags]
            itemlist_divs = soup.find_all("div", class_="itemlist")

            bases = []
            for idx in range(min(len(titles), len(prices))):
                title = titles[idx]
                price = prices[idx]
                url_path = None

                if idx < len(itemlist_divs):
                    a_tag = itemlist_divs[idx].find("a")
                    if a_tag and "href" in a_tag.attrs:
                        url_path = a_tag["href"]

                bases.append(
                    {
                        "title": title,
                        "price": price,
                        "url": f"https://chobrod.com{url_path}" if url_path else None,
                    }
                )

            def fetch_and_merge(base):
                try:
                    detail = self._fetch_detail(base["url"]) if base["url"] else {}
                    base["gear"] = detail.get("gear")
                    base["mile"] = detail.get("mile")
                    return self.normalize_and_validate(base)
                except Exception as e:
                    logger.debug("fetch_and_merge error: %s", e)
                    return None

            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [ex.submit(fetch_and_merge, b) for b in bases]
                for fut in as_completed(futures):
                    norm = fut.result()
                    if norm:
                        yield norm

            page_num += 1
            time.sleep(random.uniform(*self.page_delay))

    def _fetch_detail(self, url):
        result = {"gear": None, "mile": None}
        if not url:
            return result
        try:
            page = requests.get(url, headers=headers, timeout=8)
            page.raise_for_status()
            soup = bs(page.content, "html.parser")
            Suspension = soup.find("div", class_="group-inline")
            if Suspension:
                txt_divs = Suspension.find_all("div", class_="txt")
                if len(txt_divs) >= 1:
                    result["gear"] = txt_divs[0].text.strip()
                if len(txt_divs) >= 2:
                    result["mile"] = txt_divs[1].text.strip()
        except Exception as e:
            logger.debug("Detail fetch error for %s : %s", url, e)
            result["error"] = str(e)
        return result

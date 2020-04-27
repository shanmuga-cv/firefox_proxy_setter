import logging
import sys
from datetime import datetime, timedelta

import requests

from firefox_proxy_setter import set_proxy
from proxy_scraper import ProxyRecord, ProxyScrapper

logging.basicConfig(level=logging.INFO)

log_level = logging.DEBUG if '--debug' in sys.argv else logging.INFO 
logging.getLogger("firefox_proxy_setter").setLevel(log_level)
logger = logging.getLogger("firefox_proxy_setter.finder")

used_proxies = set()

def poke(proxy: ProxyRecord, url="https://www.youtube.com/", timeout_seconds=5) -> bool:
    try:
        requests.get(
            url,
            proxies={k: f'http://{proxy.ip}:{proxy.port}/' for k in ['http', 'https']},
            timeout=timeout_seconds
        )
        return True
    except (
            requests.exceptions.ProxyError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError
    ) as e:
        logger.debug("poke failed due to %s: %s", type(e).__name__, proxy)
        return False


def proxy_filter(proxy: ProxyRecord):
    global used_proxies
    if proxy in used_proxies:
        logger.debug("rejecting proxy for used-once: %s", proxy)
        return False
    if proxy.country in ["China", 'Germany', 'Iran']:
        logger.debug("rejecting proxy for country: %s", proxy)
        return False
    elif proxy.since_last_update() > timedelta(minutes=60):
        logger.debug("rejecting proxy for last update: %s %s", (datetime.now() - proxy.last_updated_at), proxy)
        return False
    elif proxy.uptime_success < proxy.uptime_failure:
        logger.debug("rejecting proxy for uptime ratio: %s", proxy)
        return False
    elif proxy.uptime_failure + proxy.uptime_success < 5 and proxy.uptime_failure > 0:
        logger.debug("rejecting proxy for uptime count: %s", proxy)
        return False
    # elif (
    #         600 <= proxy.uptime_success < 750 and
    #         200 <= proxy.uptime_failure <= 300
    # ):
    #     logger.debug("rejecting proxy for suspicion: %s", proxy)
    #     return False
    else:
        used_proxies.add(proxy)
        return True


class ProxyFinder:
    def __init__(self):
        self.scraper = None
        self._initiate_scraper()

    def _initiate_scraper(self):
        self.scraper = ProxyScrapper()

    def find(self):
        while True:
            try:
                proxy = next(self.scraper)
            except StopIteration as e:
                user_response = input("Scraper finished. Starting again? [Yes]/(N)o: ").lower()
                if user_response == "n":
                    break
                self._initiate_scraper()
                proxy = next(self.scraper)

            if not (proxy_filter(proxy) and poke(proxy)):
                continue
            else:
                logger.info(f"setting proxy {repr(proxy)}")
                set_proxy(proxy.ip, proxy.port)
                user_response = input("Need more? [Yes]/(N)o/(R)estart: ").lower()
                if user_response == 'n':
                    break
                elif user_response == 'r':
                    logger.info("Restarting scraper")
                    self._initiate_scraper()


if __name__ == "__main__":
    ProxyFinder().find()

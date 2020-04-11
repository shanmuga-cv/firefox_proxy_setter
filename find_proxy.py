import logging
from datetime import datetime, timedelta

import requests

from firefox_proxy_setter import set_proxy
from proxy_scraper import ProxyRecord, ProxyScrapper

logging.basicConfig(level=logging.INFO)

logging.getLogger("firefox_proxy_setter").setLevel(logging.INFO)
logger = logging.getLogger("firefox_proxy_setter.finder")

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
    if proxy.country in ["China", 'Germany', 'Iran']:
        logger.debug("rejecting proxy for country: %s", proxy)
        return False
    elif proxy.since_last_update() > timedelta(minutes=60):
        logger.debug("rejecting proxy for last update: %s %s", (datetime.now() - proxy.last_updated_at), proxy)
        return False
    elif proxy.uptime_success < proxy.uptime_failure:
        logger.debug("rejecting proxy for uptime ratio: %s", proxy)
        return False
    elif proxy.uptime_failure + proxy.uptime_success < 5:
        logger.debug("rejecting proxy for uptime count: %s", proxy)
        return False
    # elif (
    #         600 <= proxy.uptime_success < 750 and
    #         200 <= proxy.uptime_failure <= 300
    # ):
    #     logger.debug("rejecting proxy for suspicion: %s", proxy)
    #     return False
    else:
        return True


for proxy in ProxyScrapper(35):
    if not (proxy_filter(proxy) and poke(proxy)):
        continue
    else:
        logger.info(f"setting proxy {repr(proxy)}")
        set_proxy(proxy.ip, proxy.port)
        should_continue = input("Need more?")
        if should_continue.lower() == 'n':
            break

import logging
from datetime import datetime, timedelta

import requests

from fireox_proxy_setter import set_proxy
from proxy_scraper import ProxyRecord, ProxyScrapper

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("proxy_setter")
logger.setLevel(logging.INFO)


def poke(proxy: ProxyRecord, url="https://www.youtube.com/", timeout_seconds=5) -> bool:
    try:
        requests.get(
            url,
            proxies={k: f'http://{proxy.ip}:{proxy.port}/' for k in ['http', 'https']},
            timeout=timeout_seconds
        )
        return True
    except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout) as e:
        logger.debug("poke failed for: %s", proxy)
        return False


def proxy_filter(proxy: ProxyRecord):
    if proxy.country in ["China", "Indonesia", 'Germany', 'Iran']:
        logger.debug("rejecting proxy for country: %s", proxy)
        return False
    elif proxy.since_last_update() > timedelta(minutes=60):
        logger.debug("rejecting proxy for last update: %s %s", (datetime.now() - proxy.last_updated_at), proxy)
        return False
    elif proxy.uptime_success < proxy.uptime_failure * 2:
        logger.debug("rejecting proxy for uptime ratio: %s", proxy)
        return False
    elif proxy.uptime_failure + proxy.uptime_success < 20:
        logger.debug("rejecting proxy for uptime count: %s", proxy)
        return False
    elif (
            600 <= proxy.uptime_success < 750 and
            200 <= proxy.uptime_failure <= 300
    ):
        logger.debug("rejecting proxy for suspicion: %s", proxy)
        return False
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

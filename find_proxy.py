import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("proxy_setter")
from datetime import datetime, timedelta

from proxy_scraper import ProxyRecord, ProxyScrapper
from fireox_proxy_setter import set_proxy, unset_proxy

def proxy_filter(proxy: ProxyRecord):
    if proxy.country in ["China", "Indonesia", 'Germany', 'Iran']:
        logger.debug("rejecting proxy for country: %s", proxy)
        return False
    elif proxy.since_last_update() > timedelta(minutes=25):
        logger.debug("rejecting proxy for last update: %s %s",(datetime.now() - proxy.last_updated_at), proxy)
        return False
    elif proxy.uptime_success < proxy.uptime_failure:
        logger.debug("rejecting proxy for uptime ratio: %s", proxy)
        return False
    elif proxy.uptime_failure + proxy.uptime_success < 20:
        logger.debug("rejecting proxy for uptime count: %s", proxy)
        return False
    elif (600<= proxy.uptime_success <750  and 200 <= proxy.uptime_failure <= 300):
        logger.debug("rejecting proxy for suspicion: %s", proxy)
        return False
    else:
        return True

for proxy in ProxyScrapper(35):
    if not proxy_filter(proxy):
        continue
    else:
        logger.info(f"setting proxy {repr(proxy)}")
        set_proxy(proxy.ip, proxy.port)
        should_continue = input("Need more?")
        if should_continue.lower() == 'n':
            break

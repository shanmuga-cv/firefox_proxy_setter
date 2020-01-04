import logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("proxy_setter")
from datetime import datetime, timedelta

from proxy_scraper import ProxyRecord, ProxyScrapper
from fireox_proxy_setter import set_proxy, unset_proxy

def proxy_filter(proxy: ProxyRecord):
    if proxy.country in ["China", "Indonesia", 'Germany'] or \
        datetime.now() - proxy.last_updated_at > timedelta(minutes=15) or \
        proxy.uptime_success < proxy.uptime_failure*2 or \
        proxy.uptime_failure + proxy.uptime_success < 20 or \
        (3000 < proxy.uptime_success < 5000 and 100 < proxy.uptime_failure < 500):
        return False
    else:
        return True

for proxy in ProxyScrapper(3):
    if not proxy_filter(proxy):
        continue
    else:
        logger.info(f"setting proxy {repr(proxy)}")
        set_proxy(proxy.ip, proxy.port)
        should_continue = input("Need more?")
        if not should_continue in ('y', 'Y'):
            break

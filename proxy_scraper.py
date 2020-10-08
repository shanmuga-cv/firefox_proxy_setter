import logging
import re
from datetime import timedelta, datetime
from typing import Generator

import requests
from lxml import html

logger = logging.getLogger("firefox_proxy_setter.proxy_scprapper")


class ProxyRecord:
    def __init__(self, last_updated_at, ip, port, level, country, uptime_success, uptime_failure, response_time):
        self.last_updated_at = last_updated_at
        self.ip = ip
        self.port = port
        self.level = level
        self.country = country
        self.uptime_success = uptime_success
        self.uptime_failure = uptime_failure
        self.response_time = response_time

    def __repr__(self):
        return f"ProxyRecord(last_update {self.last_updated_at}, {self.ip}, {self.port}, {self.level}, {self.country}, " + \
               f"{self.uptime_success}/{self.uptime_failure}, {self.response_time}ms)"

    def since_last_update(self):
        return datetime.now() - self.last_updated_at

    def __hash__(self):
        return hash((self.ip, self.port))

    def __eq__(self, other):
        return isinstance(other, type(self)) and (self.ip, self.port) == (other.ip, other.port)


class Scraper:
    def scrape(self) -> Generator[ProxyRecord, None, None]:
        raise NotImplementedError


class GatherProxyScrapper(Scraper):
    def __init__(self):
        pass

    def scrape(self):
        pageIdx = 1
        max_pages = None
        while max_pages is None or pageIdx <= max_pages:
            logger.info(f"making http call with pageIdx {pageIdx}")
            response = requests.post("https://proxygather.com/proxylist/anonymity/?t=Elite", data={
                'PageIdx': pageIdx, 'Type': 'elite'
            })
            element = html.fromstring(response.text)
            if max_pages is None:
                max_pages = self.calculate_max_page(element)
            table_rows = element.xpath('//table[@id="tblproxy"]/tr[position()>2]')
            for tr in table_rows:
                yield self.parse(tr)
            pageIdx += 1

    @staticmethod
    def calculate_max_page(html_element):
        last_page_idx_str = html_element.xpath('//div[@class="pagenavi"]/a[last()]/text()')[0]
        return int(last_page_idx_str)

    @staticmethod
    def parse(html_element):
        row_values = html_element.xpath("./td")

        last_update_row, ip_row, port_row, level_row, country_row, city_row, uptime_row, response_time_row = row_values
        last_update_text = last_update_row.xpath("./text()")[0]
        last_update_values = re.search(r"(?P<minutes>\d+)m (?P<seconds>\d+)s ago", last_update_text).groupdict()
        last_updated_at = datetime.now() - timedelta(**{k: int(v) for k, v in
                                                        last_update_values.items()})  # possible bug timestamp of request should be used instead on datetime.now()

        ip_row_text = ip_row.xpath("./script/text()")[0]
        ip = re.search(r"document\.write\('(.+)'\)", ip_row_text).group(1)

        port_row_text = port_row.xpath("./script/text()")[0]
        port_hex_str = re.search(r"document\.write\(gp\.dep\('(.+)'\)\)", port_row_text).group(1)
        port = int(port_hex_str, 16)

        level = level_row.xpath("./text()")[0]

        country = country_row.xpath("./text()")[0]

        uptime_success, uptime_failure = [int(x) for x in uptime_row.xpath("./span/text()")]

        response_time = int(re.search(r"(\d+)ms", response_time_row.xpath("./text()")[0]).group(1))

        return ProxyRecord(last_updated_at, ip, port, level, country, uptime_success, uptime_failure, response_time)


class FreeProxyListScraper(Scraper):
    def scrape(self) -> Generator[ProxyRecord, None, None]:
        response = requests.get("https://free-proxy-list.net/")
        scrape_time = datetime.now()
        element = html.fromstring(response.text)
        table_rows = element.xpath('//table[@id="proxylisttable"]/tbody/tr')
        for tr in table_rows:
            proxy_record = self.parse(tr, scrape_time)
            if proxy_record.level == 'elite proxy':
                yield proxy_record
        logger.debug("no more proxy in the list")

    @staticmethod
    def parse(table_row, scrape_time):
        [ip, port, country_code, country, anonymity, google, https, last_checked] = [x.text for x in table_row.xpath("./td")]
        port = int(port)
        match = re.match(r'((?P<hours>\d+) hours?)?( ?(?P<minutes>\d+) minutes?)?( ?(?P<seconds>\d+) seconds?)? ago', last_checked)
        if not  match:
            raise ValueError(f"Could not parse last_checked: {last_checked}")
        duration_groupdict = {k: int(v) if v is not None else 0 for k,v in match.groupdict().items()}
        last_updated_at = scrape_time - timedelta(**duration_groupdict)
        return ProxyRecord(
            last_updated_at=last_updated_at,
            ip=ip,
            port=port,
            level=anonymity,
            country=country,
            uptime_success=None,
            uptime_failure=None,
            response_time=None,
        )

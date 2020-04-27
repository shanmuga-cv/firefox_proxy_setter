import logging
import re
from datetime import timedelta, datetime

import requests
from lxml import html

logger = logging.getLogger("ProxyScprapper")


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

    @classmethod
    def from_html(cls, html_element):
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

        return cls(last_updated_at, ip, port, level, country, uptime_success, uptime_failure, response_time)


class GatherProxyScrapper:
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
                yield ProxyRecord.from_html(tr)
            pageIdx += 1

    @staticmethod
    def calculate_max_page(html_element):
        last_page_idx_str = html_element.xpath('//div[@class="pagenavi"]/a[last()]/text()')[0]
        return int(last_page_idx_str)

import requests
from lxml import html
import re
from datetime import timedelta, datetime

import logging
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
    
    @classmethod
    def from_html(cls, html_element):
        row_values = html_element.xpath("./td")

        last_update_row, ip_row, port_row, level_row, country_row, city_row, uptime_row, response_time_row = row_values
        last_update_text = last_update_row.xpath("./text()")[0]
        last_update_values = re.search(r"(?P<minutes>\d+)m (?P<seconds>\d+)s ago", last_update_text).groupdict()
        last_updated_at = datetime.now() - timedelta(**{k: int(v) for k, v in last_update_values.items()})  # possible bug timestamp of request should be used instead on datetime.now()

        ip_row_text = ip_row.xpath("./script/text()")[0]
        ip = re.search(r"document\.write\('(.+)'\)", ip_row_text).group(1)

        port_row_text = port_row.xpath("./script/text()")[0]
        port_hex_str= re.search(r"document\.write\(gp\.dep\('(.+)'\)\)", port_row_text).group(1)
        port = int(port_hex_str, 16)

        level = level_row.xpath("./text()")[0]

        country = country_row.xpath("./text()")[0]

        uptime_success, uptime_failure = [int(x) for x in uptime_row.xpath("./span/text()")]

        response_time = int(re.search(r"(\d+)ms", response_time_row.xpath("./text()")[0]).group(1))

        return cls(last_updated_at, ip, port, level, country, uptime_success, uptime_failure, response_time)


def ProxyScrapper(max_pages=5):
    pageIdx = 1
    while pageIdx <= max_pages:
        logger.info(f"making http call with pageIdx {pageIdx}")
        response = requests.post("http://www.gatherproxy.com/proxylist/anonymity/?t=Elite", data={
            'PageIdx': pageIdx, 'Type': 'elite'
        })
        element = html.fromstring(response.text)
        table_rows = element.xpath('//table[@id="tblproxy"]/tr[position()>2]')
        for tr in table_rows:
            yield ProxyRecord.from_html(tr)
        pageIdx+=1

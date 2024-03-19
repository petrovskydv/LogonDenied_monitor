import contextlib
import logging
import time
from datetime import datetime
from ipaddress import IPv4Network, AddressValueError
from pprint import pprint
from urllib.error import HTTPError

import pywintypes
from ipwhois import BaseIpwhoisException
from pydantic.dataclasses import dataclass
from python_retry import retry
# from win32ctypes.pywin32 import pywintypes

from settings import Settings
from utils.geo_ip import GeoIp, get_ip_location
from utils.kerio import format_host_for_kerio, Kerio
from utils.read_logs import read_log, save_number

logger = logging.getLogger(__name__)


@dataclass
class AddressGroup:
    id: str
    name: str


smtp_blacklist = AddressGroup(id='c210cF9ibGFja2xpc3Q=', name='smtp_blacklist')
local_blacklist = AddressGroup(id='bG9jYWwgYmxhY2tsaXN0', name='LOCAL BLACKLIST')
russian_blacklist = AddressGroup(id='cnVzc2lhbiBmZWRlcmF0aW9u', name='Russian Federation')
usa_blacklist = AddressGroup(id='dW5pdGVkIHN0YXRlcw==', name='United States')


def handle(eventlog_server, kerio_client):
    allowed_countries: dict[str: AddressGroup] = {
        'RU': russian_blacklist,
        'US': usa_blacklist,
    }

    hosts, last_event_number = read_log(eventlog_server)
    addresses = []
    for host in hosts:
        with contextlib.suppress(BaseIpwhoisException):
            host_geo_ip: GeoIp = get_ip_location(host)
            print(host_geo_ip)
            if host_geo_ip.asn_cidr:
                try:
                    print('ip count:', IPv4Network(host_geo_ip.asn_cidr).num_addresses)
                except AddressValueError:
                    pass

            addresses.append(host_geo_ip)

    kerio_hosts = []
    for host in addresses:
        blocked_at = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        if host.asn_country_code in allowed_countries:
            template = format_host_for_kerio(
                allowed_countries[host.asn_country_code].id,
                allowed_countries[host.asn_country_code].name,
                host.query,
                f'{host.asn_description},  {host.country}, blocked_at:{blocked_at}'
            )
        elif host.asn_cidr:
            template = format_host_for_kerio(
                smtp_blacklist.id,
                smtp_blacklist.name,
                host.asn_cidr,
                f'{host.asn_description},  {host.country}'
            )
        else:
            template = format_host_for_kerio(
                local_blacklist.id,
                local_blacklist.name,
                host.query,
                f'{host.asn_description},  {host.country}, blocked_at:{blocked_at}'
            )
        kerio_hosts.append(template)

    pprint(kerio_hosts)

    if kerio_hosts:
        save_address_to_kerio(kerio_client, kerio_hosts)

    save_number(last_event_number)


@retry(
    retry_on=(HTTPError,),
    max_retries=2,
    backoff_factor=1,
    retry_logger=logger,
    # supress_exception=True,
)
def save_address_to_kerio(kerio_client, addresses):
    with contextlib.closing(kerio_client):
        kerio_client.login()
        kerio_client.save_addresses(addresses)


if __name__ == "__main__":
    settings = Settings()
    kerio_client = Kerio(settings.kerio_server, settings.kerio_username, settings.kerio_password)
    while True:
        exceptions = [pywintypes.error]
        with contextlib.suppress(*exceptions):
            handle(settings.eventlog_server, kerio_client)
            time.sleep(settings.read_event_timeout_sec)

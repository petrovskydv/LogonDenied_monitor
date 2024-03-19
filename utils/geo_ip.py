import functools
import logging
from typing import Optional

import ipwhois
from geoip import geolite2
from ipwhois import HTTPLookupError
from ipwhois.utils import get_countries
from pydantic.dataclasses import dataclass
from python_retry import retry

logger = logging.getLogger(__name__)


@dataclass
class GeoIp:
    query: str
    asn_cidr: Optional[str]
    asn_country_code: str
    asn_description: Optional[str]
    country: str = ''


@retry(
    retry_on=(HTTPLookupError,),
    max_retries=1,
    backoff_factor=1,
    # retry_logger=logger,
    # supress_exception=True,
)
@functools.lru_cache(maxsize=2000)
def get_ip_location(ip):
    try:
        wh = ipwhois.IPWhois(ip, timeout=1)
        res = wh.lookup_whois()
        host = GeoIp(**res, country=countries[res['asn_country_code']])
        if host.asn_cidr == 'NA':
            host.asn_cidr = ''
        return host
    except HTTPLookupError:
        res = geolite2.lookup(ip)
        return GeoIp(query=res.ip, asn_cidr='', asn_country_code=res.country, asn_description=res.timezone,
                     country=countries[res.country])


countries = get_countries()

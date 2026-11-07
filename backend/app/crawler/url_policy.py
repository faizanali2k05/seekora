import ipaddress
import socket
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class UnsafeUrlError(ValueError):
    pass


TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def canonicalize_url(raw_url: str) -> str:
    parsed = urlsplit(raw_url.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("Only absolute HTTP(S) URLs are allowed")
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower().rstrip(".")
    port = parsed.port
    netloc = (
        host
        if port is None or (scheme, port) in {("http", 80), ("https", 443)}
        else f"{host}:{port}"
    )
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
    ]
    path = parsed.path or "/"
    return urlunsplit((scheme, netloc, path, urlencode(sorted(query_items)), ""))


def validate_public_host(hostname: str) -> None:
    try:
        addresses = {
            item[4][0] for item in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise UnsafeUrlError("Host cannot be resolved") from exc
    if not addresses:
        raise UnsafeUrlError("Host cannot be resolved")
    for raw_address in addresses:
        address = ipaddress.ip_address(raw_address)
        if not address.is_global:
            raise UnsafeUrlError("Private or non-routable hosts are not allowed")


def validate_public_url(raw_url: str) -> str:
    canonical = canonicalize_url(raw_url)
    hostname = urlsplit(canonical).hostname
    assert hostname is not None
    validate_public_host(hostname)
    return canonical

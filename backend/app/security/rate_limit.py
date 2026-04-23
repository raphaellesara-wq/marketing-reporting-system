from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit by IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

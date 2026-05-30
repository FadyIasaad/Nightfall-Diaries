# Legacy compatibility shim. New code should import from tbt_config instead.
try:
    from tbt_config import *
except ImportError:
    pass

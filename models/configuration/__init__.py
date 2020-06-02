from .model import Configuration


def config():
    c = Configuration.query.first()
    c.mollie = c.mollie_api_key if c else None
    return c

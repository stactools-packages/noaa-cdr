from pystac import Item

from .. import stac


def create_item(href: str) -> Item:
    return stac.create_item(href)

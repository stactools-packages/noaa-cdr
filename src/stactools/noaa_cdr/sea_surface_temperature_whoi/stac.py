from pathlib import Path
from typing import List

import dateutil.relativedelta
import fsspec
import numpy
import xarray
from pystac import Collection, Item
from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr.profile import BandProfile

from .. import cog, dataset, stac, time
from ..constants import DEFAULT_CATALOG_TYPE
from .constants import CITATION, DESCRIPTION, DOI, EXTENT, ID, TITLE

TIME_WINDOW_HALF_WIDTH_IN_MINUTES = int(3 * 60 / 2)


def create_items(href: str, directory: str) -> List[Item]:
    base_item = stac.create_item(href)
    items = list()
    with fsspec.open(href) as file:
        with xarray.open_dataset(file) as ds:
            variables = dataset.data_variable_names(ds)
            profiles = dict()
            for variable in variables:
                profiles[variable] = BandProfile.build(
                    ds, variable, lambda d: d.isel(time=0).squeeze()
                )
            for i, dt in enumerate(
                time.datetime64_to_datetime(dt) for dt in ds.time.values
            ):
                item = base_item.clone()
                item.id = f"{item.id}-{i}"
                item.datetime = dt
                item.common_metadata.start_datetime = (
                    dt
                    - dateutil.relativedelta.relativedelta(
                        minutes=TIME_WINDOW_HALF_WIDTH_IN_MINUTES
                    )
                )
                item.common_metadata.end_datetime = (
                    dt
                    + dateutil.relativedelta.relativedelta(
                        minutes=TIME_WINDOW_HALF_WIDTH_IN_MINUTES
                    )
                )
                for variable in variables:
                    values = numpy.flipud(ds[variable].isel(time=i).values.squeeze())
                    values = numpy.roll(values, int(profiles[variable].width / 2), 1)
                    path = Path(directory) / f"{item.id}-{variable}.tif"
                    asset = cog.write(values, str(path), profiles[variable])
                    item.assets[variable] = asset
                items.append(item)

    return items


def create_collection() -> Collection:
    collection = Collection(
        id=ID,
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=DEFAULT_CATALOG_TYPE,
    )

    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = DOI
    scientific.citation = CITATION

    return collection

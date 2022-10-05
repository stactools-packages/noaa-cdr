import datetime
import os.path
from dataclasses import dataclass
from typing import Any, Dict, Hashable, List, Optional

import fsspec
import numpy
import xarray
from pystac import Asset

from .. import cog, dataset, time
from ..profile import BandProfile
from ..time import TimeResolution
from .constants import BASE_TIME


@dataclass(frozen=True)
class Cog:
    """Dataclass to hold the result of a cogification operation."""

    asset: Asset
    profile: BandProfile
    time_resolution: TimeResolution
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    datetime: datetime.datetime
    attributes: Dict[Hashable, Any]

    def time_interval_as_str(self) -> str:
        """Returns this COG's time interval as a string."""
        return self.time_resolution.as_str(self.datetime)

    def item_id(self) -> str:
        """Returns the item id."""
        depth = int(self.attributes["geospatial_vertical_max"])
        return f"ocean-heat-content-{self.time_interval_as_str()}-{depth}m"

    def asset_key(self) -> str:
        """Returns this COG's asset key."""
        parts = []
        for part in self.attributes["id"].split("_"):
            if part == "anomaly":
                break
            else:
                parts.append(part)
        return "_".join(parts)


def cogify(
    href: str, outdir: Optional[str] = None, latest_only: bool = False
) -> List[Cog]:
    if outdir is None:
        outdir = os.path.dirname(href)
    cogs = list()
    with fsspec.open(href) as file:
        with xarray.open_dataset(file, decode_times=False) as ds:
            time_resolution = TimeResolution.from_value(ds.time_coverage_resolution)
            variable = dataset.data_variable_name(ds)
            num_records = len(ds[variable].time)
            for i, month_offset in enumerate(ds[variable].time):
                if latest_only and i < (num_records - 1):
                    continue
                dt = time.add_months_to_datetime(BASE_TIME, month_offset)
                start_datetime, end_datetime = time_resolution.datetime_bounds(dt)
                suffix = time_resolution.as_str(dt)
                path = os.path.join(
                    outdir,
                    f"{os.path.splitext(os.path.basename(href))[0]}_{suffix}.tif",
                )
                profile = BandProfile.build(
                    ds, variable, lambda d: d.isel(time=i).squeeze()
                )
                values = numpy.flipud(ds[variable].isel(time=i).values.squeeze())
                asset = cog.write(
                    values,
                    path,
                    profile,
                )
                cogs.append(
                    Cog(
                        asset=asset,
                        profile=profile,
                        time_resolution=time_resolution,
                        datetime=dt,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        attributes=ds.attrs,
                    )
                )
    return cogs

import datetime
import os.path
from dataclasses import dataclass
from typing import Any, Dict, Hashable, List, Optional

import fsspec
import numpy
import xarray
from pystac import Asset
from stactools.core.io import ReadHrefModifier

from .. import cog, dataset, time
from ..profile import BandProfile
from ..time import TimeResolution
from .constants import BASE_TIME


@dataclass(frozen=True)
class Cog:
    """Dataclass to hold the result of a cogification operation."""

    href: str
    profile: BandProfile
    time_resolution: TimeResolution
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    datetime: datetime.datetime
    attributes: Dict[Hashable, Any]

    def asset(self) -> Asset:
        return self.profile.cog_asset(self.href)

    def time_interval_as_str(self) -> str:
        """Returns this COG's time interval as a string."""
        return self.time_resolution.as_str(self.datetime)

    def item_id(self) -> str:
        """Returns the item id."""
        return f"ocean-heat-content-{self.time_interval_as_str()}-{self.max_depth()}m"

    def asset_key(self) -> str:
        """Returns this COG's asset key."""
        parts = []
        for part in self.attributes["id"].split("_"):
            if part == "anomaly":
                break
            else:
                parts.append(part)
        return "_".join(parts)

    def interval(self) -> str:
        """Returns this cog's interval, e.g. "yearly"."""
        return self.time_resolution.to_interval()

    def max_depth(self) -> int:
        """Returns this cog's max depth."""
        return int(self.attributes["geospatial_vertical_max"])


def cogify(
    href: str,
    outdir: Optional[str] = None,
    latest_only: bool = False,
    read_href_modifier: Optional[ReadHrefModifier] = None,
    cog_hrefs: Optional[List[str]] = None,
) -> List[Cog]:
    if outdir is None:
        outdir = os.path.dirname(href)
    cogs = list()
    if read_href_modifier:
        maybe_modified_href = read_href_modifier(href)
    else:
        maybe_modified_href = href
    if cog_hrefs:
        cog_file_names = dict((os.path.basename(h), h) for h in cog_hrefs)
    else:
        cog_file_names = dict()
    with fsspec.open(maybe_modified_href) as file:
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
                file_name = (
                    f"{os.path.splitext(os.path.basename(href))[0]}_{suffix}.tif"
                )
                profile = BandProfile.build(
                    ds, variable, lambda d: d.isel(time=i).squeeze()
                )
                if file_name in cog_file_names:
                    cog_href = cog_file_names[file_name]
                else:
                    cog_href = os.path.join(outdir, file_name)
                    values = numpy.flipud(ds[variable].isel(time=i).values.squeeze())
                    cog.write(
                        values,
                        cog_href,
                        profile,
                    )
                cogs.append(
                    Cog(
                        href=cog_href,
                        profile=profile,
                        time_resolution=time_resolution,
                        datetime=dt,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        attributes=ds.attrs,
                    )
                )
    return cogs

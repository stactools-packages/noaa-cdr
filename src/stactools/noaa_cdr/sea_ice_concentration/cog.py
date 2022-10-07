from typing import Any, Dict, List

from pystac import Asset

from .. import cog
from ..profile import BandProfile
from .constants import SPATIAL_RESOLUTION

KEYS_WITH_CLASSES = [
    "cdr_seaice_conc",
    "nsidc_bt_seaice_conc",
    "stdev_of_cdr_seaice_conc",
    "temporal_interpolation_flag",
]
KEYS_WITH_BITFIELDS = ["qa_of_cdr_seaice_conc", "spatial_interpolation_flag"]


def cogify(href: str, directory: str) -> Dict[str, Asset]:
    return cog.cogify(href, directory, SeaIceConcentrationBandProfile)


class SeaIceConcentrationBandProfile(BandProfile):
    def update_cog_asset(self, key: str, asset: Asset) -> Asset:
        asset.extra_fields["raster:bands"][0]["spatial_resolution"] = SPATIAL_RESOLUTION
        if key in KEYS_WITH_CLASSES:
            asset.extra_fields["classification:classes"] = self.classes()
        elif key in KEYS_WITH_BITFIELDS:
            asset.extra_fields["classification:bitfields"] = self.bitfield()
        return asset

    def classes(self) -> List[Dict[str, Any]]:
        if "flag_values" in self.attrs:
            values = self.attrs["flag_values"]
        elif "flag_masks" in self.attrs:
            values = self.attrs["flag_masks"]
        else:
            raise ValueError(
                "could not find 'flag_values' or 'flag_masks' in self.attrs"
            )
        meanings = self.attrs["flag_meanings"].split(" ")
        classes = list()
        for value, meaning in zip(values, meanings):
            classes.append({"value": int(value), "name": meaning})
        return classes

    def bitfield(self) -> List[Dict[str, Any]]:
        if "flag_mask_meanings" in self.attrs:
            meanings = self.attrs["flag_mask_meanings"].split(" ")
        elif "flag_meanings" in self.attrs:
            meanings = self.attrs["flag_meanings"].split(" ")
        else:
            raise ValueError(
                "could not find 'flag_mask_meanings' or 'flag_meanings' in self.attrs"
            )
        bitfields = list()
        for i, meaning in enumerate(meanings):
            parts = meaning.split("_")
            parts.insert(len(parts) - 1, "not")
            not_meaning = "_".join(parts)
            bitfields.append(
                {
                    "name": meaning,
                    "offset": i,
                    "length": 1,
                    "classes": [
                        {"name": not_meaning, "value": 0},
                        {
                            "name": meaning,
                            "value": 1,
                        },
                    ],
                }
            )
        return bitfields

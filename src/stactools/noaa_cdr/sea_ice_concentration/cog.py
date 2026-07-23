from typing import Any, Dict, List, Optional

from pystac import Asset

from .. import cog
from ..profile import BandProfile
from .constants import SPATIAL_RESOLUTION

# Variables expected to carry CF `flag_values`/`flag_meanings` attributes
# describing a fixed set of discrete classes. Note: starting in V5, NSIDC
# removed the embedded land-mask flag values (251-255) from cdr_seaice_conc
# in favor of the dedicated surface_type_mask variable, so we don't expect
# classes on cdr_seaice_conc/raw_bt_seaice_conc/raw_nt_seaice_conc anymore
# -- confirmed against a real V6 file. cdr_seaice_conc_interp_temporal_flag
# DOES carry a full flag_values/flag_meanings enumeration (31 discrete
# composed values), also confirmed against a real file -- despite reading
# like a "computed" encoding in the User Guide prose, NSIDC enumerates it
# explicitly in the file. If any of this is wrong for a given file,
# classes() degrades gracefully (see below) instead of failing the COG run.
VARIABLES_WITH_CLASSES = [
    "surface_type_mask",
    "cdr_seaice_conc_interp_temporal_flag",
]
# Variables expected to carry CF `flag_masks`/`flag_meanings` (or
# `flag_mask_meanings`) attributes describing an additive bitmask.
VARIABLES_WITH_BITFIELDS = [
    "cdr_seaice_conc_qa_flag",
    "cdr_seaice_conc_interp_spatial_flag",
]
# cdr_seaice_conc_interp_temporal_flag's values are a composed 1-2 digit
# encoding (days-in-past, days-in-future) rather than a fixed enumerated
# list or bitmask, per the V6 User Guide -- not modeled with the
# classification extension here.


def cogify(href: str, directory: str) -> Dict[str, Asset]:
    return cog.cogify(href, directory, SeaIceConcentrationBandProfile)


class SeaIceConcentrationBandProfile(BandProfile):
    def cog_asset(self, href: str) -> Asset:
        asset = super().cog_asset(href)
        asset.extra_fields["raster:bands"][0]["spatial_resolution"] = SPATIAL_RESOLUTION
        if self.variable in VARIABLES_WITH_CLASSES:
            classes = self.classes()
            if classes is not None:
                asset.extra_fields["classification:classes"] = classes
        elif self.variable in VARIABLES_WITH_BITFIELDS:
            bitfield = self.bitfield()
            if bitfield is not None:
                asset.extra_fields["classification:bitfields"] = bitfield
        return asset

    def classes(self) -> Optional[List[Dict[str, Any]]]:
        if "flag_values" in self.attrs:
            values = self.attrs["flag_values"]
        elif "flag_masks" in self.attrs:
            values = self.attrs["flag_masks"]
        else:
            # The file didn't carry the flag_values/flag_masks attribute we
            # expected for this variable. Rather than fail the whole COG
            # run, skip classification metadata for this one asset.
            return None
        meanings = self.attrs["flag_meanings"].split(" ")
        classes = list()
        for value, meaning in zip(values, meanings):
            classes.append({"value": int(value), "name": meaning})
        return classes

    def bitfield(self) -> Optional[List[Dict[str, Any]]]:
        if "flag_mask_meanings" in self.attrs:
            meanings = self.attrs["flag_mask_meanings"].strip().split(" ")
        elif "flag_meanings" in self.attrs:
            meanings = self.attrs["flag_meanings"].strip().split(" ")
        else:
            return None
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

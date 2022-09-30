from typing import Iterator


def iter_noaa_hrefs() -> Iterator[str]:
    """Iterates over NOAA hrefs for this CDR."""

    for variable in [
        "heat_content",
        "mean_halosteric_sea_level",
        "mean_salinity",
        "mean_temperature",
        "mean_thermosteric_sea_level",
        "mean_total_steric_sea_level",
    ]:
        for depth in ["100", "700", "2000"]:
            for period in ["monthly", "pentad", "seasonal", "yearly"]:
                if period == "monthly" and variable != "heat_content":
                    continue
                elif depth == "100" and variable not in [
                    "mean_salinity",
                    "mean_temperature",
                ]:
                    continue
                yield (
                    "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data/0164586/"
                    f"derived/{variable}_anomaly_0-{depth}_{period}.nc"
                )

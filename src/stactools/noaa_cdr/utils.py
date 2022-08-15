import datetime
import math

import dateutil.relativedelta


def add_months_to_datetime(
    base_time: datetime.datetime, months: float
) -> datetime.datetime:
    """Adds a (possibly fractional) number of months to a datetime.

    Dateutil's relativedelta does not handle fractional numbers of months:
    https://dateutil.readthedocs.io/en/stable/relativedelta.html. This utility
    function enables fractional month offsets.

    Args:
        base_time (datetime.datetime): The start datetime.
        months (float): The number of months to advance.

    Returns:
        datetime.datetime: The new datetime.
    """
    fractional_months, integer_months = math.modf(months)
    time = base_time + dateutil.relativedelta.relativedelta(months=int(integer_months))
    if fractional_months != 0.0:
        time_in_seconds = time.timestamp()
        next_month_in_seconds = (
            time + dateutil.relativedelta.relativedelta(months=1)
        ).timestamp()
        return time + dateutil.relativedelta.relativedelta(
            seconds=int((next_month_in_seconds - time_in_seconds) * fractional_months)
        )
    else:
        return time

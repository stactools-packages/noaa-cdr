from typing import List

from xarray import Dataset


def data_variable_name(dataset: Dataset) -> str:
    """Returns the variable name that points to a three or four-dimensional data array.

    Args:
        dataset (xarray.Dataset): An open xarray Dataset
    Returns:
        str: The variable name.
    """
    names = list(data_variable_names(dataset))
    if not names:
        raise ValueError("No 4-dimensional variable found in this dataset.")
    elif len(names) == 1:
        return names[0]
    else:
        raise ValueError(
            f"Multiple 4-dimensional variables found in this dataset: {names}"
        )


def data_variable_names(dataset: Dataset) -> List[str]:
    """Returns a list of the variable names that point to a
    three or four dimensional data array.

    Args:
        dataset (xarray.Dataset): An open xarray Dataset
    Returns:
        List[str]: List of the variable names.
    """
    return list(
        str(variable)
        for variable in dataset.variables
        if len(dataset[variable].sizes) in (3, 4)
    )

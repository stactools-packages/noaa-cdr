from xarray import Dataset


def data_variable_name(dataset: Dataset) -> str:
    """Returns the variable name that points to a four-dimensional data array.
    Args:
        dataset (xarray.Dataset): An open xarray Dataset
    Returns:
        str: The variable name.
    """
    for variable in dataset.variables:
        if len(dataset[variable].sizes) == 4:
            return str(variable)
    raise Exception("No 4-dimensional variable found in this dataset.")

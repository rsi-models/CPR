import csv


def get_params(file, numerical_key=False):
    """
    Create dictionary from csv file.

    Parameters
    ----------
    file : _io.TextIOWrapper
        csv file
    numerical_key : bool, optional
        numerical key, by default False

    Returns
    -------
    dict
        dictionary of parameters
    """
    d_params = {}
    with open(file) as params:
        rows = csv.reader(params)
        next(rows)
        for row in rows:
            var, value, var_type, _ = row
            if var_type == 'int':
                d_params[var] = int(value)
            elif var_type == 'float':
                d_params[var] = float(value)
            elif var_type == 'bool':
                d_params[var] = bool(int(value))
            else:
                d_params[var] = value
    if numerical_key:
        d_params = {int(k): v for k, v in d_params.items()}
    return d_params


def add_params_as_attr(inst, file):
    """
    Add parameters to class instance.

    Parameters
    ----------
    inst : object
        class instance
    file : _io.TextIOWrapper
        csv file
    """
    d_params = get_params(file)
    inst.__dict__.update(d_params)


def change_params(inst, extra_params):
    """
    Update value of some parameters in inst to values of extra_params.

    Parameters
    ----------
    inst: dict
        parameters
    extra_params: dict
        parameters to be updated and their new values
    """
    new_params = {k: v for k, v in extra_params.items() if k in vars(inst)}
    for k, v in new_params.items():
        setattr(inst, k, v)


def create_nom_real(year, prices):
    """
    Create two functions that convert prices from real to nominal
    and from nominal to real, with base year 2018.

    Parameters
    ----------
    year : int
        year
    prices : Prices
        instance of the class Prices

    Returns
    -------
    function
        function converting nominal to real
    function
        function converting real to nominal
    """
    factor = prices.d_infl_factors[year]

    def nom(x):
        return x * factor

    def real(x):
        return x / factor

    return nom, real


def create_nom(year, prices):
    """
    Create function that converts prices from real to nominal,
    with base year 2018.

    Parameters
    ----------
    year : int
        year
    prices : Prices
        instance of the class Prices

    Returns
    -------
    function
        function converting real to nominal
    """
    factor = prices.d_infl_factors[year]

    def nom(x):
        return x * factor

    return nom


def create_real(year, prices):
    """
    Create function that convert prices from nominal to real,
    with base year 2018.

    Parameters
    ----------
    year : int
        year
    prices : Prices
        instance of the class Prices

    Returns
    -------
    function
        function converting nominal to real
    """
    factor = prices.d_infl_factors[year]

    def real(x):
        return x / factor

    return real

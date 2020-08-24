import csv


def get_params(file, numerical_key = False):
    """
    Creates dictionary from csv file with two columns (name, value) infering
    data types with pandas
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
    d_params = get_params(file)
    inst.__dict__.update(d_params)


def change_params(inst, extra_params):
    new_params = {k: v for k, v in extra_params.items() if k in inst.__dict__}
    for k, v in new_params.items():
        setattr(inst, k, v)


def create_nom_real(year, prices):
    factor = prices.d_infl_factors[year]

    def nom(x):
        return x * factor

    def real(x):
        return x / factor

    return nom, real


def create_nom(year, prices):
    factor = prices.d_infl_factors[year]

    def nom(x):
        return x * factor

    return nom


def create_real(year, prices):
    factor = prices.d_infl_factors[year]

    def real(x):
        return x / factor

    return real


def create_nom_real_2016(year, prices):
    factor = prices.d_infl_factors[year] / prices.d_infl_factors[2016]

    def nom(x):
        return x * factor

    def real(x):
        return x / factor

    return nom, real


def create_nom_2016(year, prices):
    factor = prices.d_infl_factors[year] / prices.d_infl_factors[2016]

    def nom(x):
        return x * factor

    return nom


def create_real_2016(year, prices):
    factor = prices.d_infl_factors[year] / prices.d_infl_factors[2016]

    def real(x):
        return x / factor

    return real

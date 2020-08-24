import numpy as np


class Debt():
    """
    Manages all debts in nominal terms.

    :type name: float
    :param name: Name of the debt account.

    :type d_params: Dictionnary
    :param d_params: Dictionnary with all the household informations0.

    :type init_rate: float
    :param init_rate: Initial interest rate.

    :type max_term: float
    :param max_term: Maximum term.
    """
    def __init__(self, name, d_hh, common, prices):
        self.name = name
        self.init_balance = d_hh[name]
        self.init_m_payment = d_hh[name + '_payment']
        self.init_term = self.compute_init_term(common, prices)
        self.reset()

    def compute_init_term(self, common, prices):
        """
        Computes the initial term in years.

        :type max_term: integer
        :param max_term: Maximum term.

        rtype: float
        """
        init_rate = prices.d_interest_debt[self.name][0, 0]
        init_monthly_rate = (1 + init_rate)**(1/12) - 1
        interest = init_monthly_rate / (1+init_monthly_rate) \
            * self.init_balance
        init_m_payment = max(self.init_m_payment, interest + 1e-12)
        # debt is explosive if init_payment lower than interest
        term_months = (np.log(init_m_payment /
                       (init_m_payment - interest)) /
                       np.log(1+init_monthly_rate))
        return min(np.ceil(term_months/12), common.max_term_debts)

    def update(self, year, rate, prices):
        """
        Updates yearly payment, balance using yearly rate
        and inflation_factor.

        :type common: object
        :param common: Instance of the Common class.

        :type rate: float
        :param rate: Interest rate
        """
        self.inflation_factor = prices.d_infl_factors[year]
        if self.term == 0:
            self.payment, self.balance = 0, 0
        else:
            self.payment = (self.balance*(rate/(1+rate)) /
                            (1 - (1/(1+rate))**self.term))
            new_bal = max(self.balance - self.payment, 0)
            self.balance = new_bal * (1 + rate)
            self.term -= 1

    def reset(self):
        """
        Resets the personal loan and the inflation_factor
        to its initial values.
        """
        self.balance = self.init_balance
        self.term = self.init_term

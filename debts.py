import numpy as np


class Debt():
    """
    This class manages all debts. All amounts are nominal.
    """
    def __init__(self, name, d_hh, common, prices):
        self.name = name
        self.init_balance = d_hh[name]
        self.init_m_payment = d_hh[name + '_payment']
        self.init_term = self.estimate_init_term(common, prices)
        self.reset()

    def estimate_init_term(self, common, prices):
        """
        Estimate the term of the debt.

        Parameters
        ----------
        common : Common
            instance of the class Common
        prices : Prices
            instance of the class Prices

        Returns
        -------
        int
            term of the debt
        """
        init_rate = prices.d_interest_debt[self.name][0, 0]
        init_monthly_rate = (1 + init_rate)**(1/12) - 1
        interest = init_monthly_rate / (1 + init_monthly_rate) \
            * self.init_balance
        init_m_payment = max(self.init_m_payment, interest + 1e-12)
        # debt is explosive if init_payment lower than interest
        term_months = (np.log(init_m_payment / (init_m_payment - interest))
                       / np.log(1 + init_monthly_rate))
        return min(np.ceil(term_months / 12), common.max_term_debts)

    def update(self, year, rate, prices):
        """
        Updates yearly payment and balance.

        Parameters
        ----------
        year : int
            year
        rate : float
            interest rate
        prices : Prices
            instance of the class Prices
        """
        if self.term == 0:
            self.payment, self.balance = 0, 0
        else:
            self.payment = (self.balance*(rate/(1 + rate)) /
                            (1 - (1 / (1 + rate))**self.term))
            new_bal = max(self.balance - self.payment, 0)
            self.balance = new_bal * (1 + rate)
            self.term -= 1

    def reset(self):
        """
        Reset balance and term to initial values.
        """
        self.balance = self.init_balance
        self.term = self.init_term

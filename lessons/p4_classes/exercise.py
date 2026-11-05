"""P4 exercise."""
from contextlib import contextmanager  # noqa: F401
from dataclasses import dataclass  # noqa: F401


# 1) A frozen dataclass `Money(amount: int, currency: str = "USD")`.
#    - Money(5) + Money(7) == Money(12)
#    - adding different currencies raises CurrencyMismatch (below)
#    - it must be hashable (frozen=True) so it can live in a set
class Money:  # TODO: turn me into a frozen dataclass with __add__
    pass


# 2) Exception hierarchy:
#    WalletError(Exception)                 - base
#    CurrencyMismatch(WalletError)
#    InsufficientFunds(WalletError)         - has a `.shortfall: int` attribute
class WalletError(Exception):
    pass


class CurrencyMismatch(Exception):  # 🐛 should inherit from WalletError
    pass


class InsufficientFunds(WalletError):
    pass  # TODO: __init__(self, shortfall) storing self.shortfall and a helpful message


# 3) Wallet
#    w = Wallet("ada")                -> owner "ada", empty, currency "USD"
#    w.deposit(Money(500))
#    w.withdraw(Money(200))           -> raises InsufficientFunds(shortfall=...) if not enough
#    w.balance                        -> Money(300)   (a read-only @property)
#    len(w)                           -> number of transactions (deposits + withdrawals)
#    repr(w)                          -> "Wallet(owner='ada', balance=300)"
#    Wallet.from_dict({"owner": "ada", "deposits": [100, 50]})  -> classmethod
class Wallet:
    def __init__(self, owner: str, currency: str = "USD"):
        raise NotImplementedError


# 4) transaction(wallet): a context manager. Inside the block you can deposit/withdraw;
#    if the block raises, the wallet's balance AND history are restored, and the error propagates.
@contextmanager
def transaction(wallet):
    raise NotImplementedError
    yield

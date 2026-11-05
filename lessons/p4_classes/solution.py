"""P4 reference solution."""
from contextlib import contextmanager
from dataclasses import dataclass


class WalletError(Exception):
    """Base class for every wallet problem."""


class CurrencyMismatch(WalletError):
    pass


class InsufficientFunds(WalletError):
    def __init__(self, shortfall: int):
        super().__init__(f"insufficient funds: short by {shortfall}")
        self.shortfall = shortfall


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "USD"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatch(f"{self.currency} != {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)


class Wallet:
    def __init__(self, owner: str, currency: str = "USD"):
        self.owner = owner
        self.currency = currency
        self._history: list[Money] = []

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        wallet = cls(data["owner"], data.get("currency", "USD"))
        for amount in data.get("deposits", []):
            wallet.deposit(Money(amount, wallet.currency))
        return wallet

    @property
    def balance(self) -> Money:
        total = Money(0, self.currency)
        for entry in self._history:
            total = total + entry
        return total

    def deposit(self, money: Money) -> None:
        if money.currency != self.currency:
            raise CurrencyMismatch(f"wallet is {self.currency}")
        self._history.append(money)

    def withdraw(self, money: Money) -> None:
        if money.currency != self.currency:
            raise CurrencyMismatch(f"wallet is {self.currency}")
        shortfall = money.amount - self.balance.amount
        if shortfall > 0:
            raise InsufficientFunds(shortfall)
        self._history.append(-money)

    def __len__(self) -> int:
        return len(self._history)

    def __repr__(self) -> str:
        return f"Wallet(owner={self.owner!r}, balance={self.balance.amount})"


@contextmanager
def transaction(wallet: Wallet):
    snapshot = list(wallet._history)
    try:
        yield wallet
    except Exception:
        wallet._history = snapshot  # roll back, then let the error propagate
        raise

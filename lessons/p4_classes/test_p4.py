import dataclasses

import pytest

from support import target

m = target(__file__)


def test_money_is_a_frozen_dataclass():
    assert dataclasses.is_dataclass(m.Money)
    a = m.Money(5)
    assert a.currency == "USD"
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.amount = 10
    assert m.Money(5) + m.Money(7) == m.Money(12)
    assert len({m.Money(1), m.Money(1), m.Money(2)}) == 2


def test_money_currency_mismatch():
    with pytest.raises(m.CurrencyMismatch):
        m.Money(1, "USD") + m.Money(1, "EUR")


def test_exception_hierarchy():
    assert issubclass(m.CurrencyMismatch, m.WalletError)
    assert issubclass(m.InsufficientFunds, m.WalletError)
    err = m.InsufficientFunds(30)
    assert err.shortfall == 30 and "30" in str(err)


def test_wallet_basics():
    w = m.Wallet("ada")
    w.deposit(m.Money(500))
    w.withdraw(m.Money(200))
    assert w.balance == m.Money(300)
    assert len(w) == 2
    assert repr(w) == "Wallet(owner='ada', balance=300)"
    with pytest.raises(AttributeError):
        w.balance = m.Money(1_000_000)  # read-only property


def test_wallet_insufficient_funds():
    w = m.Wallet("ada")
    w.deposit(m.Money(100))
    with pytest.raises(m.InsufficientFunds) as info:
        w.withdraw(m.Money(130))
    assert info.value.shortfall == 30
    assert w.balance == m.Money(100)


def test_wallet_from_dict():
    w = m.Wallet.from_dict({"owner": "ada", "deposits": [100, 50]})
    assert w.owner == "ada" and w.balance == m.Money(150) and len(w) == 2


def test_transaction_rolls_back_on_error():
    w = m.Wallet("ada")
    w.deposit(m.Money(100))
    with pytest.raises(m.InsufficientFunds):
        with m.transaction(w):
            w.deposit(m.Money(50))
            w.withdraw(m.Money(1000))
    assert w.balance == m.Money(100) and len(w) == 1

    with m.transaction(w):
        w.deposit(m.Money(1))
    assert w.balance == m.Money(101)

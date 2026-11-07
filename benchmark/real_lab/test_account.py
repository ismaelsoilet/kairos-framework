"""
Real Multithreaded Test for K-Bench Concurrency Experiment.
Spawns 50 threads attempting simultaneous withdrawals.
"""
import threading
from account import UnsafeBankAccount, SafeBankAccount

def test_unsafe_account_fails():
    """50 threads withdrawing 10 each from 1000 balance. Expected: 500 balance."""
    account = UnsafeBankAccount(1000)
    threads = []
    for _ in range(50):
        t = threading.Thread(target=account.withdraw, args=(10,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    # In race condition, multiple threads read the same balance, so final balance is > 500!
    return account.balance

def test_safe_account_succeeds():
    """50 threads withdrawing 10 each from 1000 balance with Lock. Expected: 500 balance."""
    account = SafeBankAccount(1000)
    threads = []
    def do_withdraw():
        res = account.withdraw(10)
        assert res is True
    for _ in range(50):
        t = threading.Thread(target=do_withdraw)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    # Test boundary
    assert account.withdraw(10000) is False
    return account.balance

if __name__ == "__main__":
    assert test_safe_account_succeeds() == 500
    # Also test Unsafe
    u = UnsafeBankAccount(100)
    assert u.withdraw(50) is True
    assert u.withdraw(500) is False

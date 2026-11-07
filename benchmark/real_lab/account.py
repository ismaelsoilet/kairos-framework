"""
Target Service: Bank Account balance manager.
Used for K-Bench real concurrency experiments.
"""
import time
import threading

class UnsafeBankAccount:
    """Intentionally flawed bank account subject to race conditions."""
    def __init__(self, balance: int = 1000):
        self.balance = balance

    def withdraw(self, amount: int):
        if self.balance >= amount:
            # Simulate slight I/O or network delay causing race condition
            current = self.balance
            time.sleep(0.0001)
            self.balance = current - amount
            return True
        return False

class SafeBankAccount:
    """Thread-safe bank account protected by a mutex lock."""
    def __init__(self, balance: int = 1000):
        self.balance = balance
        self._lock = threading.Lock()

    def withdraw(self, amount: int):
        with self._lock:
            if self.balance >= amount:
                current = self.balance
                time.sleep(0.0001)
                self.balance = current - amount
                return True
            return False

import hashlib
import random, math
from sympy import mod_inverse, gcd

# TEMPORARY HASHING FUNCTION

class ChameleonHash:
    def __init__(self, prime=None, generator=3):
        """Initialize the Chameleon Hash function with a prime and generator."""
        self.p = prime if prime else (2**127 - 1)  # Default large prime
        self.g = generator  # Generator of the group
        self.trapdoor = random.randint(2, self.p - 1)  # Secret trapdoor (private key)

    def compute_hash(self, message: str, r: int, trapdoor: int) -> str:
        """Compute chameleon hash and return it as a hex string."""
        m = int.from_bytes(message.encode(), 'big') % self.p
        hash_value = (pow(self.g, m, self.p) * pow(r, trapdoor, self.p)) % self.p  # Compute modular hash
        return hex(hash_value)  # ✅ Convert to hex string

    # def find_collision(self, original_message: str, new_message: str, original_r: int, trapdoor: int) -> int:
    #     """Finds a new value r' so that we can modify a block without changing the hash"""
    #     m_old = int.from_bytes(original_message.encode(), 'big') % self.p
    #     m_new = int.from_bytes(new_message.encode(), 'big') % self.p
        
    #     # Solve for r' using modular arithmetic
    #     exponent = (m_old - m_new) % (self.p - 1)
    #     inverse_exponent = pow(self.g, -exponent, self.p)  # Compute modular inverse
    #     new_r = (original_r * inverse_exponent) % self.p  # Compute new r'

    #     print(f"✅ Collision found! New r' = {new_r}")
    #     return new_r

    def find_collision(self, original_message: str, new_message: str, original_r: int, trapdoor: int) -> int:
        """Finds a new value r' that preserves the original hash after modification."""

        m_old = int.from_bytes(original_message.encode(), 'big') % self.p
        m_new = int.from_bytes(new_message.encode(), 'big') % self.p

        print(f"🔍 find_collision() Debug Info:")
        print(f"   - m_old: {m_old}")
        print(f"   - m_new: {m_new}")
        print(f"   - original_r: {original_r}")
        print(f"   - trapdoor: {trapdoor}")

        # Compute delta_m
        delta_m = (m_old - m_new) % (self.p - 1)

        # Compute exponentiation factor safely
        try:
            exponent = (delta_m * mod_inverse(trapdoor, self.p - 1)) % (self.p - 1)
        except ValueError:
            print("⚠️ Warning: Trapdoor is not invertible. Choosing a new trapdoor.")
            
            # Find a new trapdoor that is coprime with p-1
            while True:
                trapdoor = random.randint(2, 10**6)
                if gcd(trapdoor, self.p - 1) == 1:
                    break
            
            exponent = (delta_m * mod_inverse(trapdoor, self.p - 1)) % (self.p - 1)

        # Solve for r'
        r_prime = (original_r * pow(self.g, exponent, self.p)) % self.p

        print(f"   - New r': {r_prime}")

        return r_prime
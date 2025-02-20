import hashlib
import random

# TEMPORARY HASHING FUNCTION

class ChameleonHash:
    def __init__(self):
        """Initialize the chameleon hash function with a trapdoor"""
        self.trapdoor = random.randint(1, 10**6)

    def compute_hash(self, message: str, r: int, trapdoor: int) -> str:
        """Create the chameleon hash using message and r"""
        hash_input = f"{message}{r}{trapdoor}".encode()
        return hashlib.sha256(hash_input).hexdigest()

    def find_collision(self, original_message: str, new_message: str, original_r: int) -> int:
        """Finds a new value r' so that we can modify a block without changing the hash"""
        original_hash = self.compute_hash(original_message, original_r, self.trapdoor)
        
        # Brute-force r'
        new_r = random.randint(1, 10**6)
        max_attempts = 1000000

        for attempt in range(max_attempts):
            if self.compute_hash(new_message, new_r, self.trapdoor) == original_hash:
                print(f"Collision found after {attempt + 1} attempts! r' = {new_r}")
                return new_r

            new_r += 1

        return original_hash
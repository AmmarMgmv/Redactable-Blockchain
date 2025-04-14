import json, time
import numpy as np
from chameleon import (
    generate_ring_lwe_keys, 
    chameleon_hash_ring_lwe, 
    find_collision_ring_lwe,
    poly_mul_mod
)

class Block:
    def __init__(self, index, previous_hash, data):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = int(time.time())
        self.data = data
        self.modification_history = []
        
        # Generate Ring-LWE Chameleon Hash Keys for this block
        # Using smaller n for efficiency while maintaining security
        self.poly_a, self.poly_s, self.poly_b, self.q, self.poly_mod = generate_ring_lwe_keys(n=128, error_bound=1)
        
        # Store the error polynomial for collision finding
        # In a real implementation, we might want to encrypt this or store securely
        self.poly_e = (self.poly_b - poly_mul_mod(self.poly_a, self.poly_s, self.q, self.poly_mod)) % self.q
        self.poly_e = np.where(self.poly_e > self.q/2, self.poly_e - self.q, self.poly_e)  # Recover small errors
        
        # Generate randomness for hashing (random polynomial r)
        self.n = len(self.poly_a)
        self.random_poly = np.random.randint(0, self.q, size=self.n, dtype=np.int64)
        
        # Calculate and store the original hash
        self.hash = self.calculate_hash()
        # Store original hash separately to ensure we're always comparing against the same value
        self.original_hash = self.hash

    def calculate_hash(self):
        """Calculate the Ring-LWE chameleon hash for this block"""
        return chameleon_hash_ring_lwe(
            self.poly_a, 
            self.poly_b, 
            self.data, 
            self.random_poly, 
            self.q, 
            self.poly_mod
        )

    def modify_block(self, new_data, editor_trapdoor):
        """
        Modify block data while preserving the hash value using Ring-LWE chameleon hash
        
        Args:
            new_data: The new data to replace current block data
            editor_trapdoor: The trapdoor key (poly_s) needed for authorized modifications
            
        Returns:
            Boolean indicating success or failure
        """
        # Verify trapdoor key matches stored secret polynomial
        if not np.array_equal(editor_trapdoor, self.poly_s):
            print("Unauthorized modification attempt!")
            return False

        # Use the stored original hash for consistency
        target_hash = self.original_hash
        
        max_attempts = 10
        collision_found = False
        
        for attempt in range(max_attempts):
            # Find collision to maintain hash value
            new_random_poly = find_collision_ring_lwe(
                self.poly_a, 
                self.poly_s, 
                self.poly_b, 
                self.q, 
                self.poly_mod,
                self.data, 
                new_data, 
                self.random_poly
            )
            
            # Temporarily update and check hash
            old_data = self.data
            old_random_poly = self.random_poly
            
            self.data = new_data
            self.random_poly = new_random_poly
            
            new_hash = self.calculate_hash()
            
            if new_hash == target_hash:
                collision_found = True
                break
            else:
                # Restore previous state and try again with a different approach
                self.data = old_data
                self.random_poly = old_random_poly
                print(f"Attempt {attempt+1} failed, trying again...")
        
        if collision_found:
            # Store previous data in modification history
            self.modification_history.append({
                "old_data": old_data, 
                "new_data": new_data, 
                "timestamp": int(time.time())
            })
            
            print("Ring-LWE Chameleon Hash successfully preserved the block hash.")
            print(f"Preserved hash: {target_hash[:15]}...")
            return True
        else:
            print("ERROR: Ring-LWE Chameleon Hash failed to maintain consistency after multiple attempts!")
            print(f"Target hash: {target_hash[:15]}...")
            print(f"Last attempted hash: {new_hash[:15]}...")
            
            # Restore original state
            self.data = old_data
            self.random_poly = old_random_poly
            return False


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "0", "Genesis Block")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        latest_block = self.get_latest_block()
        new_block = Block(len(self.chain), latest_block.hash, data)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify hash integrity
            expected_hash = current_block.calculate_hash()
            if current_block.hash != expected_hash:
                print(f"Block {i} has been tampered with!")
                return False

            # Ensure previous hash consistency
            if current_block.previous_hash != previous_block.hash:
                print(f"Block {i} has an invalid previous hash!")
                return False

        print("Blockchain is valid!")
        return True

    def print_chain(self):
        """Prints the full blockchain in a formatted manner"""
        for block in self.chain:
            computed_hash = block.calculate_hash()
            print(f"\nBlock {block.index}")
            print(f"Timestamp: {block.timestamp}")
            print(f"Data: {block.data}")
            print(f"Original Hash: {block.hash[:15]}...")
            print(f"Computed Hash: {computed_hash[:15]}...")
            print(f"Previous Block Hash: {block.previous_hash[:15]}...")
            print(f"Modification History: {len(block.modification_history)} changes")
            if block.modification_history:
                for i, mod in enumerate(block.modification_history):
                    print(f"  Change {i+1}: '{mod['old_data']}' → '{mod['new_data']}'")
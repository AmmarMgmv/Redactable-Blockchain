import json, time
import numpy as np
from chameleon import generate_keys, chameleon_hash, find_collision

class Block:
    def __init__(self, index, previous_hash, data):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = int(time.time())
        self.data = data
        self.modification_history = []
        
        # Generate LWE-based Chameleon Hash Keys with smaller dimension for simplicity
        self.matrix_A, self.vector_s, self.vector_b, self.q, self.vector_e = generate_keys(n=256, q=8192, error_bound=4)   
        
        # Generate randomness for hashing (random vector r)
        self.n = self.matrix_A.shape[0]
        self.random_vector = np.random.randint(0, self.q, size=(self.n, 1), dtype=np.int64)
        
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculate the LWE-based chameleon hash for this block"""
        return chameleon_hash(self.matrix_A, self.vector_b, self.data, self.random_vector, self.q)

    def modify_block(self, new_data, editor_trapdoor):
        """
        Modify block data while preserving the hash value using LWE-based chameleon hash
        
        Args:
            new_data: The new data to replace current block data
            editor_trapdoor: The trapdoor key (vector_s) needed for authorized modifications
            
        Returns:
            Boolean indicating success or failure
        """
        print("\n======== BLOCK MODIFICATION PROCESS ========")
        print(f"Attempting to modify block {self.index} from:")
        print(f"  '{self.data}' to")
        print(f"  '{new_data}'")
        
        # Verify trapdoor key (simple check for equality)
        trapdoor_valid = np.array_equal(editor_trapdoor, self.vector_s)
        print(f"Trapdoor verification: {'Valid' if trapdoor_valid else 'Invalid'}")
        
        if not trapdoor_valid:
            print("Unauthorized modification attempt!")
            return False

        # Store original hash for verification
        original_hash = self.hash
        print(f"Original block hash: {original_hash}")
        
        # Let's also verify the hash calculation works properly with the current data
        verification_hash = chameleon_hash(self.matrix_A, self.vector_b, self.data, self.random_vector, self.q, debug=True)
        print(f"Verification hash matches: {verification_hash == original_hash}")
        
        # Find collision using our LWE approach, passing the error vector
        new_random_vector = find_collision(
            self.matrix_A, self.vector_s, self.vector_b, self.q,
            self.data, new_data, self.random_vector, self.vector_e
        )
        
        # Store previous data before modification
        self.modification_history.append({
            "old_data": self.data, 
            "new_data": new_data, 
            "timestamp": int(time.time())
        })

        # Update block data and randomness
        self.data = new_data
        self.random_vector = new_random_vector
        
        print("\n== Final Verification ==")
        # Verify hash preservation
        recalculated_hash = self.calculate_hash()
        print(f"Original hash:   {original_hash}")
        print(f"Recalculated hash: {recalculated_hash}")
        
        if recalculated_hash != original_hash:
            print("ERROR: LWE-based Chameleon Hash failed to maintain consistency!")
            print(f"Original hash: {original_hash[:15]}...")
            print(f"New hash: {recalculated_hash[:15]}...")
            return False
        else:
            print("SUCCESS: LWE-based Chameleon Hash successfully preserved the block hash.")
            print(f"Preserved hash: {original_hash[:15]}...")
            return True


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
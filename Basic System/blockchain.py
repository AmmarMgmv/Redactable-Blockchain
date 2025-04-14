import json, time, random
from chameleon import generate_keys, chameleon_hash, find_collision

class Block:
    def __init__(self, index, previous_hash, data):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = int(time.time())
        self.data = data
        self.modification_history = []
        # Generate Chameleon Hash Keys for this block
        self.prime_p, self.prime_q, self.generator_g, self.public_key, self.trapdoor_key = generate_keys()
        # Generate randomness for hashing
        self.random_value = self.generate_random_value()
        self.s_value = random.randint(1, self.prime_q - 1)  # New s_value
        self.hash = self.calculate_hash()

    def generate_random_value(self):
        return int(time.time()) % self.prime_q  

    # Get hash using r and s values
    def calculate_hash(self):
        return chameleon_hash(self.public_key, self.prime_p, self.prime_q, 
                              self.generator_g, self.data, self.random_value, self.s_value)

    # Allow modifications with valid trapdoor key w/out changing hash value
    def modify_block(self, new_data, editor_trapdoor):
        if editor_trapdoor != self.trapdoor_key:
            print("Unauthorized modification attempt!")
            return False

        # Generate new randomness and new s_value
        new_random_value, new_s_value = find_collision(self.public_key, self.trapdoor_key,
                                                       self.prime_p, self.prime_q, self.generator_g,
                                                       self.data, new_data, 
                                                       self.random_value, self.s_value)

        # Store previous data before modification
        self.modification_history.append({"old_data": self.data, "new_data": new_data, "timestamp": int(time.time())})

        # Update block data and randomness
        self.data = new_data
        self.random_value = new_random_value
        self.s_value = new_s_value

        recalculated_hash = self.calculate_hash()
        # Check if recalculated hash still matches the stored one
        if recalculated_hash != self.hash:
            print("ERROR: Chameleon Hash failed to maintain consistency!")
        else:
            print("Chameleon Hash successfully preserved the block hash.")

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
            print(f"Public Key: {block.public_key}")
            print(f"Original Hash: {block.hash[:15]}...")
            print(f"Computed Hash: {computed_hash[:15]}...")
            print(f"Previous Block Hash: {block.previous_hash[:15]}...")
            print(f"Modification History: {block.modification_history}\n")
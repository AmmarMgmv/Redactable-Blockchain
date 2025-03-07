import hashlib
import time
import random
from user import User
from voting import VotingSystem
from chameleon_hash import ChameleonHash
from sympy import gcd

# Represents a single block in the blockchain
class Block:
    def __init__(self, index, previous_hash, data, chameleon_hash, r=None):
        self.index = index                                              # Position in blockchain    
        self.previous_hash = previous_hash                              # Hash of previous block       
        self.data = data                                                # Block content
        self.chameleon_hash = chameleon_hash                            # Chameleon Hash instance
        self.r = r if r is not None else random.randint(1, 1000000)     # Random value for chameleon hashing

        # Ensure trapdoor is coprime with (p-1)
        while True:
            candidate_trapdoor = random.randint(2, 10**6)  # Avoid 1 to prevent trivial cases
            if gcd(candidate_trapdoor, self.chameleon_hash.p - 1) == 1:
                self.trapdoor = candidate_trapdoor
                break

        self.timestamp = time.time()                                    # Time block was created at
        self.hash = self.compute_hash()                                 # Generate block's hash
        self.modification_history = []                                  # Track block modifications
        
    def compute_hash(self):
        """Get the chameleon hash for the block"""
        message = f"{self.previous_hash}{self.data}"
        return self.chameleon_hash.compute_hash(message, self.r, self.trapdoor)

    # def modify_block(self, new_data, user: User, blockchain):
    #     # Check if they have permission to modify blocks
    #     if not user.can_modify_blocks:
    #         print(f"{user.name} doesn't have modification permissions, requesting vote...")
        
    #     # Start voting
    #     proposal_id = blockchain.voting_system.start_voting(self.index, new_data, user)
    #     if proposal_id is None:
    #         print(f"Modification request by {user.name} failed.")
    #         return

    #     print(f"\nWaiting for votes on Proposal {proposal_id}...")

    #     # Consortium members vote randomly
    #     for voter in blockchain.users.values():
    #         if voter.is_consensus_member:
    #             blockchain.voting_system.cast_vote(proposal_id, voter, decision=random.choice([True, False]))

    #     proposer, selected_editor = blockchain.voting_system.count_votes(proposal_id)

    #     # Count the votes
    #     if proposer and selected_editor:
    #         print(f"✅ Proposal Approved! {selected_editor} is assigned as the editor for Block {self.index}.")

    #         blockchain.users[selected_editor].private_key = self.trapdoor  # ✅ Selected editor now has the block's trapdoor
    #         blockchain.users[selected_editor].can_modify_blocks = True  # ✅ Grant modification permission
    #         # Apply modification if approved
    #         original_data = self.data
    #         original_r = self.r
    #         new_r = self.chameleon_hash.find_collision(original_data, new_data, original_r, blockchain.users[selected_editor].private_key)

    #         if new_r is None:
    #             print(f"❌ Modification failed: Unable to compute valid r'. Aborting change.")
    #             return

    #         self.data = new_data
    #         self.r = new_r
    #         self.hash = self.compute_hash()

    #         # Update next blocks hash
    #         block_index = self.index
    #         if block_index < len(blockchain.chain) - 1:
    #             next_block = blockchain.chain[block_index + 1]
    #             next_block.previous_hash = self.hash
    #             next_block.hash = next_block.compute_hash()

    #         # Log modification
    #         self.modification_history.append({
    #             "timestamp": time.time(),
    #             "previous_data": original_data,
    #             "new_data": new_data,
    #             "proposer": proposer,
    #             "modifier": selected_editor
    #         })
    #         print(f"Block {self.index} modified successfully by {selected_editor}!")
    #     else:
    #         print(f"Modification request for Block {self.index} was rejected.")

    def modify_block(self, new_data, user: User, blockchain):
        # Check if user has permission to modify
        if not user.can_modify_blocks:
            print(f"{user.name} doesn't have modification permissions, requesting vote...")

        # Start voting
        proposal_id = blockchain.voting_system.start_voting(self.index, new_data, user)
        if proposal_id is None:
            print(f"Modification request by {user.name} failed.")
            return

        print(f"\nWaiting for votes on Proposal {proposal_id}...")

        # Consortium members vote randomly
        for voter in blockchain.users.values():
            if voter.is_consensus_member:
                blockchain.voting_system.cast_vote(proposal_id, voter, decision=random.choice([True, False]))

        proposer, selected_editor = blockchain.voting_system.count_votes(proposal_id)

        # Count the votes
        if proposer and selected_editor:
            print(f"✅ Proposal Approved! {selected_editor} is assigned as the editor for Block {self.index}.")

            blockchain.users[selected_editor].private_key = self.trapdoor  # ✅ Selected editor now has the block's trapdoor
            blockchain.users[selected_editor].can_modify_blocks = True  # ✅ Grant modification permission

            # Compute old hash before modification
            original_data = self.data
            original_r = self.r
            old_hash = self.compute_hash()

            print(f"\n🔍 DEBUG: Before modification:")
            print(f"   - Block {self.index} Stored Hash: {self.hash}")
            print(f"   - Block {self.index} Computed Hash: {old_hash}")

            # Compute new `r'`
            new_r = self.chameleon_hash.find_collision(original_data, new_data, original_r, blockchain.users[selected_editor].private_key)

            if new_r is None:
                print(f"❌ Modification failed: Unable to compute valid r'. Aborting change.")
                return

            print(f"\n🔍 DEBUG: find_collision() results:")
            print(f"   - Original r: {original_r}")
            print(f"   - New r': {new_r}")

            # Compute new hash using the modified `r'`
            new_hash = self.chameleon_hash.compute_hash(new_data, new_r, self.trapdoor)

            print(f"\n🔍 DEBUG: After modification:")
            print(f"   - Expected New Hash: {old_hash}")
            print(f"   - Computed New Hash: {new_hash}")

            # Ensure new hash matches expected old hash
            if new_hash != old_hash:
                print("❌ Hash mismatch! Collision failed. Modification aborted.")
                return

            # Apply the modification
            self.data = new_data
            self.r = new_r
            self.hash = new_hash  # ✅ Only set new hash if it matches

            # Update next blocks hash
            block_index = self.index
            if block_index < len(blockchain.chain) - 1:
                next_block = blockchain.chain[block_index + 1]
                next_block.previous_hash = self.hash
                next_block.hash = next_block.compute_hash()

            # Log modification
            self.modification_history.append({
                "timestamp": time.time(),
                "previous_data": original_data,
                "new_data": new_data,
                "proposer": proposer,
                "modifier": selected_editor
            })

            print(f"✅ Block {self.index} modified successfully by {selected_editor}!")
        else:
            print(f"Modification request for Block {self.index} was rejected.")
    
    # Make the block printable
    def __repr__(self):
        return f"Block(index={self.index}, hash={self.hash[:10]}, prev_hash={self.previous_hash[:10]})"

# Represents a blockchain as a linked list of blocks
class Blockchain:
    def __init__(self):
        self.chameleon_hash = ChameleonHash()
        self.chain = []                                                 # List to store blocks 
        self.create_genesis_block()                                     # Create first block

        # Members of the blockchain
        self.users = {
            "Alice": User(user_id="1", name="Alice", is_consensus_member=True, can_modify_blocks=False),
            "Bob": User(user_id="2", name="Bob", is_consensus_member=True, can_modify_blocks=False),
            "Charlie": User(user_id="3", name="Charlie", is_consensus_member=True, can_modify_blocks=False),
            "Eve": User(user_id="4", name="Eve", is_consensus_member=True, can_modify_blocks=False),
            "Chris": User(user_id="5", name="Chris", is_consensus_member=True, can_modify_blocks=False),
            "Liam": User(user_id="5", name="Liam", is_consensus_member=False, can_modify_blocks=False),
        }

        # Initialize voting system
        self.voting_system = VotingSystem(self)

        # All consortium members get the same trapdoor key
        for user in self.users.values():
            if user.can_modify_blocks:
                user.private_key = self.chameleon_hash.trapdoor

    def get_user_private_key(self, user_name: str):
        """Gets a user's private key"""
        if user_name in self.users:
            return self.users[user_name].private_key
        return None
    
    def create_genesis_block(self):
        """Creates the first block"""
        genesis_block = Block(index=0, previous_hash="0", data="Genesis Block", chameleon_hash=self.chameleon_hash)
        self.chain.append(genesis_block)

    def add_block(self, data):
        """Adds a new block to the blockchain"""
        previous_block = self.chain[-1]
        new_block = Block(index=len(self.chain), previous_hash=previous_block.hash, data=data, chameleon_hash=self.chameleon_hash)
        self.chain.append(new_block)

    def is_chain_valid(self):
        """Check if the blockchain is valid."""
        for i in range(1, len(self.chain)):
            prev_block = self.chain[i - 1]
            current_block = self.chain[i]

            if current_block.previous_hash != prev_block.hash:
                print(f"Chain broken at block {current_block.index}!")
                return False
            
            elif current_block.hash != current_block.compute_hash():
                print(f"Tampering detected at block {current_block.index}!")
                return False
        return True

    def print_chain(self):
        """Prints the full blockchain"""
        for block in self.chain:
            # Compute current hash
            true_hash = block.compute_hash()
            print(f"\nBlock {block.index}")
            print(f"Timestamp: {block.timestamp}")
            print(f"Data: {block.data}")
            print(f"Trapdoor: {block.trapdoor}")
            print(f"Stored Hash: {block.hash[:15]}...")
            print(f"True Hash: {true_hash[:15]}...")
            print(f"Prev Hash: {block.previous_hash[:15]}...\n")


            
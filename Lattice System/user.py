import random
import hashlib

class User:
    def __init__(self, user_id: str, name: str, is_consensus_member: bool = False, can_modify_blocks: bool = False):
        """Represents a user in the redactable blockchain system."""
        self.user_id = user_id                              # A unique ID for the user
        self.name = name                                    # Users name
        self.private_key = self.generate_private_key()      # Get private key
        self.is_consensus_member = is_consensus_member      # Whether the user can participate in voting
        self.can_modify_blocks = can_modify_blocks          # Whether the user can modify blocks
        self.vote_history = []                              # Stores a users vote history

    def generate_private_key(self):
        """Generates a trapdoor key for the user."""
        return hashlib.sha256(f"{self.user_id}{random.randint(1, 10**6)}".encode()).hexdigest()

    def vote(self, proposal_id: str, decision: bool):
        """Allows the user to vote on a blockchain edit request."""
        if not self.is_consensus_member:
            print(f"{self.name} is not authorized to vote.")
            return None

        vote_record = {"proposal_id": proposal_id, "decision": decision}
        self.vote_history.append(vote_record)
        return vote_record

    def __repr__(self):
        return f"User({self.name}, Can Modify: {self.can_modify_blocks}, Can Vote: {self.is_consensus_member})"

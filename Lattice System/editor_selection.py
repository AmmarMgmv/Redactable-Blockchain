import hashlib
import random
import time

class EditorSelection:
    def __init__(self, consortium_members):
        """Initializes the editor selection process"""
        self.members = consortium_members           # List of eligible members
        self.commitments = {}                       # Stores hashed commitments
        self.revealed_values = {}                   # Stores revealed values

    def commit_random_string(self, member_id):
        """Each member commits a secret random string as a hash"""
        secret_value = str(random.randint(1, 10**6))
        commitment = hashlib.sha256(secret_value.encode()).hexdigest()
        self.commitments[member_id] = (commitment, secret_value)
        return commitment

    def reveal_random_string(self, member_id):
        """Each member reveals their committed secret value and verifies it against the original commitment"""
        if member_id not in self.commitments:
            raise ValueError(f"Member {member_id} did not commit a value!")

        commitment, original_secret = self.commitments[member_id]

        # Make sure the revealed secret actually matches the original commitment
        revealed_secret = original_secret 
        recomputed_commitment = hashlib.sha256(revealed_secret.encode()).hexdigest()

        if recomputed_commitment != commitment:
            raise ValueError(f"Commitment mismatch! {member_id} tried to cheat!")

        # Store verified revealed value
        self.revealed_values[member_id] = revealed_secret
        return revealed_secret

    def select_editor(self):
        """Combines all revealed values, hashes them, and uses the hash output to select an editor"""
        if len(self.revealed_values) != len(self.members):
            raise ValueError("Not all members have revealed their values!")

        # Concatenate all values & hash
        combined_string = "".join(self.revealed_values.values())
        random_seed = int(hashlib.sha256(combined_string.encode()).hexdigest(), 16)

        # Use the seed to select a random editor from the members list
        editor_index = random_seed % len(self.members)
        selected_editor = self.members[editor_index]

        print(f"Editor Selected: {selected_editor} (Random Index: {editor_index})")
        return selected_editor

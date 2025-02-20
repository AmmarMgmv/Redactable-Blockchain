import time
import uuid 
from editor_selection import EditorSelection

class VotingSystem:
    def __init__(self, blockchain):
        """Initializes the voting system"""
        self.blockchain = blockchain                                                    # Reference to blockchain
        self.active_proposals = {}                                                      # Stores ongoing votes
        self.vote_history = []                                                          # Store past votes
        self.editor_selection = EditorSelection(list(self.blockchain.users.keys()))     # Initialise editor selection

    def start_voting(self, block_index, proposed_data, proposer):
        """Starts a new voting session for modifying a block"""

        # Generate unique ID
        proposal_id = str(uuid.uuid4())

        # Get eligible voters (only consortium members)
        voters = [user for user in self.blockchain.users.values() if user.is_consensus_member]

        # Check that theres at least 1 voter
        if not voters:
            print("No eligible voters available. Voting cancelled")
            return None

        # Create proposal
        self.active_proposals[proposal_id] = {
            "block_index": block_index,
            "proposed_data": proposed_data,
            "proposer": proposer.name,
            "voters": voters,
            "votes": {},
            "status": "ongoing",
            "timestamp": time.time()
        }

        print(f"\nVoting started for modifying Block {block_index} (Proposal ID: {proposal_id}).")
        print(f"Proposed by: {proposer.name}")
        print(f"Eligible voters: {[v.name for v in voters]}")
        return proposal_id

    def cast_vote(self, proposal_id, voter, decision):
        """Allows a consortium member to vote on an active proposal"""
        if proposal_id not in self.active_proposals:
            print(f"Invalid proposal ID: {proposal_id}")
            return

        proposal = self.active_proposals[proposal_id]

        if voter not in proposal["voters"]:
            print(f"{voter.name} is not eligible to vote on this proposal.")
            return

        if voter.user_id in proposal["votes"]:
            print(f"{voter.name} has already voted on this proposal.")
            return

        # Record the vote
        proposal["votes"][voter.user_id] = decision
        voter.vote_history.append({"proposal_id": proposal_id, "decision": decision})
        print(f"{voter.name} voted {'YES' if decision else 'NO'} on Proposal {proposal_id}.")

    def count_votes(self, proposal_id):
        """Counts votes for a proposal and checks if the modification is approved"""
        if proposal_id not in self.active_proposals:
            print(f"Invalid proposal ID: {proposal_id}")
            return False

        proposal = self.active_proposals[proposal_id]
        total_voters = len(proposal["voters"])
        yes_votes = sum(proposal["votes"].values())
        no_votes = total_voters - yes_votes
        # Needs 50% + 1 to accept vote
        majority_needed = (total_voters // 2) + 1

        if len(proposal["votes"]) < 3:
            print(f"Proposal REJECTED due to low participation! (Only {len(proposal['votes'])} votes cast, minimum 3 required)")
            proposal["status"] = "rejected"
            self.vote_history.append(proposal)
            del self.active_proposals[proposal_id]
            return False

        print(f"\nVote Result for Proposal {proposal_id} (Modifying Block {proposal['block_index']}):")
        print(f"YES votes: {yes_votes}")
        print(f"NO votes: {no_votes}")
        print(f"Majority needed: {majority_needed}")

        if yes_votes >= majority_needed:
            print("✅ Proposal APPROVED! Selecting an editor...")
            selected_editor = self.run_editor_selection()
            if selected_editor:
                print(f"Selected Editor: {selected_editor}")
                proposal["status"] = "approved"
                self.vote_history.append(proposal)
                del self.active_proposals[proposal_id]
                return selected_editor
            else:
                print("Error: No editor selected!")
                return False
        else:
            print("Proposal REJECTED! The modification will NOT be applied.")
            proposal["status"] = "rejected"
            self.vote_history.append(proposal)
            del self.active_proposals[proposal_id]
            return False
    
    def run_editor_selection(self):
        """Handles editor selection using the Time Capsule Mechanism"""
        all_members = list(self.blockchain.users.keys())

        print("\nCommit Phase: Members submitting their random values...")
        for member in all_members:
            self.editor_selection.commit_random_string(member)
        print("\nReveal Phase: Members revealing their random values...")
        for member in all_members:
            self.editor_selection.reveal_random_string(member)
        print("\nSelecting Editor...")
        selected_editor = self.editor_selection.select_editor()

        self.selected_editor = selected_editor
        
        # Only selected editor can modify
        for user in self.blockchain.users.values():
            user.can_modify = False
        self.blockchain.users[selected_editor].can_modify = True
        return selected_editor
    
    def print_active_proposals(self):
        """Prints all active proposals that are waiting for votes"""
        if not self.active_proposals:
            print("\nNo active proposals.")
            return

        print("\n🔹 Active Proposals:")
        for proposal_id, proposal in self.active_proposals.items():
            print(f"\nProposal ID: {proposal_id}")
            print(f"Block Index: {proposal['block_index']}")
            print(f"Proposed Data: {proposal['proposed_data']}")
            print(f"Proposed by: {proposal['proposer']}")
            print(f"Timestamp: {proposal['timestamp']}")
            print(f"Votes Cast: {len(proposal['votes'])}/{len(proposal['voters'])} voters")

    def print_vote_history(self):
        """Prints the history of all proposals and their outcomes."""
        if not self.vote_history:
            print("\nNo completed proposals in vote history.")
            return

        print("\n🔹 Vote History:")
        for proposal in self.vote_history:
            print(f"\nProposal ID: {proposal['status']}")
            print(f"Block Index: {proposal['block_index']}")
            print(f"Proposed Data: {proposal['proposed_data']}")
            print(f"Proposed by: {proposal['proposer']}")
            print(f"Timestamp: {proposal['timestamp']}")
            print(f"Status: {'APPROVED' if proposal['status'] == 'approved' else 'REJECTED'}")
            print(f"Votes: {len(proposal['votes'])}/{len(proposal['voters'])} voters")
            for voter_id, decision in proposal["votes"].items():
                voter = next((u for u in self.blockchain.users.values() if u.user_id == voter_id), None)
                voter_name = voter.name if voter else "Unknown"
                print(f"      - {voter_name} voted {'YES' if decision else 'NO'}")
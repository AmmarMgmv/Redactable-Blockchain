from blockchain import Blockchain

if __name__ == "__main__":
    blockchain = Blockchain()
    blockchain.add_block("Transaction 1: Alice pays Bob 10 BTC")
    blockchain.add_block("Transaction 2: Bob pays Charlie 5 BTC")

    print("\n--ORIGINAL CHAIN--")
    blockchain.print_chain()

    # Break the chain by modifying Block 1's previous_hash
    # print("\nBreaking the Chain at Block 1")
    # blockchain.chain[1].previous_hash = "FAKE_HASH_12345"

    # Tamper with Block 2's Data
    # print("\nTampering with Block 2's Data")
    # blockchain.chain[2].data = "Transaction 2: Bob pays Eve 100 BTC"

    # Select block to modify
    block_to_modify = blockchain.chain[1]

    # Alice proposes a vote
    alice = blockchain.users["Alice"]
    print(f"\n{alice.name} is requesting to modify Block {block_to_modify.index}...")
    block_to_modify.modify_block("Transaction 1: Alice pays Eve 20 BTC", alice, blockchain)

    print("\n--CURRENT CHAIN--")
    blockchain.print_chain()

    # Print modification history
    print(f"\nModification History of Block {block_to_modify.index}:")
    for mod in block_to_modify.modification_history:
        print(f"Proposed by: {mod['proposer']}")
        print(f"Modified by: {mod['modifier']}")
        print(f"Time: {mod['timestamp']}")
        print(f"Previous Data: {mod['previous_data']}")
        print(f"New Data: {mod['new_data']}\n")

    # Check blockchain validity
    print("\nBlockchain Valid:", blockchain.is_chain_valid())


    # print("\nPrinting Active Proposals")
    # blockchain.voting_system.print_active_proposals()

    # print("\nPrinting Vote History")
    # blockchain.voting_system.print_vote_history()
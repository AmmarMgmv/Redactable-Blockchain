from blockchain import Blockchain

def main():
    # Create a new blockchain instance
    my_blockchain = Blockchain()
    
    # Add some test blocks
    my_blockchain.add_block("Transaction A: Alice -> Bob, $50")
    my_blockchain.add_block("Transaction B: Bob -> Charlie, $30")

    # Print the blockchain
    print("\n=== Initial Blockchain ===")
    my_blockchain.print_chain()
    
    print("Blockchain valid?:", my_blockchain.is_chain_valid())

    # 🔴 Test: Modify block data without permission (invalid case)
    # test_invalid_data_modification(my_blockchain)
    
    # 🔴 Test: Tamper with a block’s previous hash (invalid case)
    # test_invalid_previous_hash(my_blockchain)

    # 🟢 Test: Modify a block correctly using Chameleon Hash (valid case)
    test_valid_block_modification(my_blockchain, block_index=1, new_data="Random new transaction")

    # 🔴 Test: Unauthorized modification attempt (invalid case)
    # test_invalid_block_modification(my_blockchain, block_index=2, new_data="Fake Transaction")

    print("Blockchain valid?:", my_blockchain.is_chain_valid())

def test_invalid_data_modification(blockchain):
    print("\n=== 🔴 Testing Data Change ===")
    testBlockchain = blockchain
    testBlockchain.chain[1].data = "Tampered Data"
    testBlockchain.print_chain()
    print("Blockchain valid:", testBlockchain.is_chain_valid())

def test_invalid_previous_hash(blockchain):
    print("\n=== 🔴 Testing Invalid Hash ===")
    testBlockchain = blockchain
    testBlockchain.chain[2].previous_hash = "FakePreviousHash"
    testBlockchain.print_chain()
    print("Blockchain valid:", testBlockchain.is_chain_valid())

# Tests block change with valid trapdoor
def test_valid_block_modification(blockchain, block_index, new_data):
    print(f"\n=== 🔴 Testing Authorized Modification of Block {block_index} ===")
    block = blockchain.chain[block_index]

    original_hash = block.hash
    success = block.modify_block(new_data, block.trapdoor_key)

    if success:
        print(f"Block {block_index} successfully modified!")
        print(f"Original Hash: {original_hash[:15]}...")
        print(f"Updated Hash:  {block.hash[:15]}...")
    else:
        print(f"Failed to modify Block {block_index}!")

    blockchain.print_chain()

# Tests block change with invalid trapdoor
def test_invalid_block_modification(blockchain, block_index, new_data):
    print(f"\n=== 🔴 Testing Unauthorized Modification of Block {block_index} ===")
    block = blockchain.chain[block_index]

    fake_trapdoor = 999999999999  # Random incorrect value
    success = block.modify_block(new_data, fake_trapdoor)

    if success:
        print(f"Unauthorized modification has occured")
    else:
        print(f"Unauthorized modification prevented")

    blockchain.print_chain()

if __name__ == "__main__":
    main()
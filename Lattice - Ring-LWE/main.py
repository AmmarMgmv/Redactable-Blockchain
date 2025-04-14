from blockchain import Blockchain
import numpy as np

def main():
    print("Initializing Quantum-Resistant Ring-LWE Blockchain")
    # Create a new blockchain instance
    my_blockchain = Blockchain()
    
    # Add some test blocks
    print("\nAdding blocks to the blockchain...")
    block1 = my_blockchain.add_block("Transaction A: Alice -> Bob, $50")
    block2 = my_blockchain.add_block("Transaction B: Bob -> Charlie, $30")
    block3 = my_blockchain.add_block("Transaction C: Charlie -> Dave, $15")

    # Print the blockchain
    print("\nInitial Blockchain State")
    my_blockchain.print_chain()
    
    # Verify blockchain integrity
    print("\nVerifying blockchain integrity...")
    is_valid = my_blockchain.is_chain_valid()
    print(f"Blockchain valid: {is_valid}")

    # Test authorized modification
    print("\nTesting authorized block modification...")
    test_valid_block_modification(my_blockchain, block_index=1, 
                                 new_data="Updated Transaction: Alice -> Bob, $75")

    # Verify blockchain integrity after modification
    # print("\nVerifying blockchain integrity after modification...")
    # is_still_valid = my_blockchain.is_chain_valid()
    # print(f"Blockchain still valid: {is_still_valid}")
    
    # # Test unauthorized modification
    # print("\nTesting unauthorized block modification...")
    # test_invalid_block_modification(my_blockchain, block_index=2, 
    #                                new_data="Fraudulent Transaction: Bob -> Mallory, $1000")

def test_valid_block_modification(blockchain, block_index, new_data):
    """Test modifying a block with valid trapdoor"""
    print(f"Attempting to modify Block {block_index}...")
    block = blockchain.chain[block_index]

    original_hash = block.hash
    # Use the correct trapdoor (poly_s) for authorized modification
    success = block.modify_block(new_data, block.poly_s)

    if success:
        print(f"Block {block_index} successfully modified!")
        print(f"Original hash preserved: {original_hash[:15]}... == {block.hash[:15]}...")
    else:
        print(f"Failed to modify Block {block_index}!")

def test_invalid_block_modification(blockchain, block_index, new_data):
    """Test modifying a block with invalid trapdoor"""
    print(f"Attempting unauthorized modification of Block {block_index}...")
    block = blockchain.chain[block_index]

    # Create a fake trapdoor (random polynomial of the same shape)
    n = len(block.poly_a)
    fake_trapdoor = np.random.randint(0, block.q, size=n, dtype=np.int64)
    
    success = block.modify_block(new_data, fake_trapdoor)

    if success:
        print(f"Security breach! Unauthorized modification succeeded.")
    else:
        print(f"Security working correctly. Unauthorized modification prevented.")

if __name__ == "__main__":
    main()
import hashlib
import random
import sympy

def generate_keys(bit_length=128):
    """
    Generates cryptographic keys for Chameleon Hashing.
    Returns:
        - prime_p: Large prime number p
        - prime_q: Prime factor of (p-1)
        - generator_g: Generator g
        - public_key: Public key (hk)
        - trapdoor_key: Secret trapdoor key (tk)
    """
    # Generate a safe prime p where p = 2q + 1 (q is also prime)
    while True:
        prime_q = sympy.randprime(2**(bit_length-2), 2**(bit_length-1))
        prime_p = 2 * prime_q + 1
        if sympy.isprime(prime_p):
            break
    
    # Find a generator for the subgroup of order q
    while True:
        h = random.randint(2, prime_p - 2)
        generator_g = pow(h, 2, prime_p)  # Ensures g has order q
        if generator_g != 1:
            break
    
    # Generate trapdoor key in range [1, q-1]
    trapdoor_key = random.randint(1, prime_q - 1)
    
    # Compute public key
    public_key = pow(generator_g, trapdoor_key, prime_p)
    
    return prime_p, prime_q, generator_g, public_key, trapdoor_key

def chameleon_hash(public_key, prime_p, prime_q, generator_g, message, r_value, s_value):
    """
    Computes the Chameleon Hash of a message.
    """
    # Ensure inputs are properly handled
    if isinstance(message, str):
        message_bytes = message.encode()
    else:
        message_bytes = message
    
    # Compute e = hash(message || r) mod q
    hash_input = message_bytes + str(r_value).encode()
    e = int.from_bytes(hashlib.sha256(hash_input).digest(), 'big') % prime_q
    
    # Ensure s_value is within range [0, q-1]
    s_value = s_value % prime_q
    
    # Compute y^e = (public_key^e mod p)
    y_to_e = pow(public_key, e, prime_p)
    
    # Compute g^s = (generator_g^s mod p)
    g_to_s = pow(generator_g, s_value, prime_p)
    
    # Compute final hash = hash((g^s * y^e) mod p)
    hash_value = (g_to_s * y_to_e) % prime_p
    
    return hashlib.sha256(str(hash_value).encode()).hexdigest()

def find_collision(public_key, trapdoor_key, prime_p, prime_q, generator_g,
                   original_message, modified_message, r1, s1):
    """
    Finds a collision for the chameleon hash using the trapdoor key.
    Uses error handling and retry logic to ensure reliable collision finding.
    """
    # Print debugging info
    # print(f"\n🔎 Debugging `find_collision()`")
    # print(f"🔹 Original Message: {original_message}")
    # print(f"🔹 Modified Message: {modified_message}")
    # print(f"🔹 Original Random Value (r1): {r1}")
    # print(f"🔹 Original s1: {s1}")
    
    # Ensure inputs are properly handled
    if isinstance(original_message, str):
        original_bytes = original_message.encode()
    else:
        original_bytes = original_message
        
    if isinstance(modified_message, str):
        modified_bytes = modified_message.encode()
    else:
        modified_bytes = modified_message
    
    # Make sure r1 and s1 are within the proper range
    r1 = r1 % prime_q
    s1 = s1 % prime_q
    
    # Get the original hash we need to match
    original_hash = chameleon_hash(public_key, prime_p, prime_q, generator_g, original_message, r1, s1)
    
    # Try up to 5 times to find a collision (to handle edge cases)
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Generate a new random r2
            r2 = random.randint(1, prime_q - 1)
            
            # Compute e1 = hash(original_message || r1) mod q
            hash_input1 = original_bytes + str(r1).encode()
            e1 = int.from_bytes(hashlib.sha256(hash_input1).digest(), 'big') % prime_q
            
            # Compute e2 = hash(modified_message || r2) mod q
            hash_input2 = modified_bytes + str(r2).encode()
            e2 = int.from_bytes(hashlib.sha256(hash_input2).digest(), 'big') % prime_q
            
            # Calculate s2 using the collision finding formula
            # s2 = s1 + (e1 - e2) * trapdoor_key mod q
            e_diff = (e1 - e2) % prime_q
            s2 = (s1 + (e_diff * trapdoor_key) % prime_q) % prime_q
            
            # Verify if new hash matches old hash
            new_hash = chameleon_hash(public_key, prime_p, prime_q, generator_g, modified_message, r2, s2)
            
            print(f"New Random Value (r2): {r2}")
            print(f"New s2: {s2}")
            print(f"Old Hash: {original_hash}")
            print(f"New Hash (should match old hash): {new_hash}")
            
            if original_hash == new_hash:
                print(f"Successfully found a valid `r2` and `s2` on attempt {attempt+1}.")
                return r2, s2
            else:
                print(f"Attempt {attempt+1}: Hashes don't match, trying again...")
                
        except Exception as e:
            print(f"Error in attempt {attempt+1}: {str(e)}")
    
    # If we reach here, we failed to find a collision after max_attempts
    print("ERROR: Failed to find a collision after multiple attempts.")
    
    # Return best effort values (though they won't produce matching hashes)
    return r2, s2
import numpy as np
import hashlib
from sympy import symbols, Poly, GF, invert, rem

# Ring-LWE Chameleon Hash Implementation with Pure SymPy
# Fixed implementation with proper seed handling

def is_prime(n):
    """Check if a number is prime"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def next_power_of_2(n):
    """Return the next power of 2 greater than or equal to n"""
    return 1 if n == 0 else 2**(n - 1).bit_length()

def ntt_params(n):
    """Generate modulus q for NTT operations"""
    if n == 256:
        return 7681
    elif n == 512:
        return 12289
    else:
        q = next_power_of_2(2*n) + 1
        while not is_prime(q):
            q += 2*n
        return q

def generate_ring_lwe_keys(n=256, error_bound=2):
    """Generate Ring-LWE keys for chameleon hashing"""
    # Set modulus q
    q = ntt_params(n)
    
    # Initialize symbolic variable
    x = symbols('x')
    
    # Define polynomial modulus x^n + 1
    mod_poly = Poly([1] + [0] * (n-1) + [1], x, domain=GF(q))
    
    # Generate random polynomial a (ensure it's invertible)
    attempt = 0
    while True:
        attempt += 1
        # Generate random coefficients
        a_coeffs = np.random.randint(1, q, size=n).tolist()
        a_poly = Poly(a_coeffs, x, domain=GF(q))
        
        try:
            # Check if a is invertible
            _ = invert(a_poly, mod_poly, domain=GF(q))
            print(f"[INFO] Found invertible poly_a after {attempt} tries.")
            break
        except Exception:
            if attempt % 100 == 0:
                print(f"[INFO] Attempt {attempt}: still searching for invertible poly_a...")
            continue
    
    # Generate small polynomials s and e
    s_coeffs = np.random.randint(-error_bound, error_bound + 1, size=n).tolist()
    e_coeffs = np.random.randint(-error_bound, error_bound + 1, size=n).tolist()
    
    # Convert to positive values modulo q if needed
    s_coeffs = [(c % q) for c in s_coeffs]
    e_coeffs = [(c % q) for c in e_coeffs]
    
    s_poly = Poly(s_coeffs, x, domain=GF(q))
    e_poly = Poly(e_coeffs, x, domain=GF(q))
    
    # Compute b = a*s + e (mod x^n + 1)
    b_poly = (a_poly * s_poly + e_poly).rem(mod_poly)
    
    # Convert back to coefficient lists for easier handling
    a_coeffs = extract_coeffs(a_poly, n, q)
    s_coeffs = extract_coeffs(s_poly, n, q)
    b_coeffs = extract_coeffs(b_poly, n, q)
    
    print(f"[DEBUG] Generated Key Coefficients:")
    print(f"  a first 5: {a_coeffs[:5]}")
    print(f"  s first 5: {s_coeffs[:5]}")
    print(f"  b first 5: {b_coeffs[:5]}")
    
    return a_coeffs, s_coeffs, b_coeffs, q, n

def extract_coeffs(poly, n, q):
    """Extract coefficients from a SymPy polynomial with proper modulo q handling"""
    # Get coefficient list (including zero coefficients)
    coeffs = []
    poly_dict = poly.as_dict()
    
    # Fill in all coefficients up to degree, including zeros
    for i in range(n):
        if (i,) in poly_dict:
            coeff = int(poly_dict[(i,)]) % q
        else:
            coeff = 0
        coeffs.append(coeff)
    
    return coeffs

def message_to_poly(message, q, n):
    """Convert a message to a polynomial in Z_q[x] with fixed seed handling"""
    if isinstance(message, str):
        message_bytes = message.encode()
    else:
        message_bytes = str(message).encode()
    
    # Hash the message to get a deterministic but seemingly random sequence
    hash_obj = hashlib.sha256(message_bytes)
    hash_bytes = hash_obj.digest()
    
    # Use the hash to create multiple 32-bit seeds and mix them
    seeds = []
    for i in range(0, min(32, len(hash_bytes)), 4):
        # Take 4 bytes (32 bits) at a time
        seed_chunk = int.from_bytes(hash_bytes[i:i+4], byteorder='little')
        seeds.append(seed_chunk)
    
    # Use the first seed to initialize the RNG
    rng = np.random.RandomState(seeds[0])
    
    # Use additional seeds to influence the output
    for seed in seeds[1:]:
        # Mix in additional entropy from each seed
        temp_rng = np.random.RandomState(seed)
        rng_state = rng.get_state()
        temp_state = temp_rng.get_state()
        # XOR the state elements where possible
        new_state = list(rng_state)
        new_state[1] = np.bitwise_xor(rng_state[1][:len(temp_state[1])], temp_state[1]) 
        rng.set_state(tuple(new_state))
    
    # Generate polynomial coefficients
    coeffs = rng.randint(0, q, size=n).tolist()
    
    return coeffs

def chameleon_hash_ring_lwe(a_coeffs, b_coeffs, message, r_coeffs, q, n, return_raw=False):
    """Compute Ring-LWE Chameleon Hash: H(m,r) = a*r + b*H(m)"""
    # Get message polynomial
    m_coeffs = message_to_poly(message, q, n)
    
    # Initialize symbolic variable
    x = symbols('x')
    
    # Define polynomial modulus x^n + 1
    mod_poly = Poly([1] + [0] * (n-1) + [1], x, domain=GF(q))
    
    # Convert coefficients to polynomials
    a_poly = Poly(a_coeffs, x, domain=GF(q))
    b_poly = Poly(b_coeffs, x, domain=GF(q))
    r_poly = Poly(r_coeffs, x, domain=GF(q))
    m_poly = Poly(m_coeffs, x, domain=GF(q))
    
    # Compute term1 = a*r mod (x^n + 1)
    term1_poly = (a_poly * r_poly).rem(mod_poly)
    
    # Compute term2 = b*m mod (x^n + 1)
    term2_poly = (b_poly * m_poly).rem(mod_poly)
    
    # Compute hash = a*r + b*m mod (x^n + 1)
    hash_poly = (term1_poly + term2_poly).rem(mod_poly)
    
    # Extract coefficients properly
    term1_coeffs = extract_coeffs(term1_poly, n, q)
    term2_coeffs = extract_coeffs(term2_poly, n, q)
    hash_coeffs = extract_coeffs(hash_poly, n, q)
    
    print(f"  Message: {message}")
    print(f"  Term1 (a*r) first 5 coeffs: {term1_coeffs[:5]}")
    print(f"  Term2 (b*m) first 5 coeffs: {term2_coeffs[:5]}")
    print(f"  Final hash polynomial first 5 coeffs: {hash_coeffs[:5]}")
    
    if return_raw:
        return hash_coeffs, m_coeffs
    
    # Finalize hash to a single digest - using only the hash coefficients
    hash_bytes = np.array(hash_coeffs[:min(len(hash_coeffs), 64)], dtype=np.int64).tobytes()
    final_hash = hashlib.sha256(hash_bytes).hexdigest()
    print(f"  Final SHA-256 Hash: {final_hash[:15]}...")
    
    return final_hash

def find_collision_ring_lwe(a_coeffs, s_coeffs, b_coeffs, q, n, 
                           original_message, modified_message, r_coeffs):
    """Find a collision for Ring-LWE chameleon hash with corrected approach"""
    print("\n[DEBUG] find_collision_ring_lwe:")
    print(f"  Original message: {original_message}")
    print(f"  Modified message: {modified_message}")
    
    # First get the message polynomials
    # Note: we need to keep these for calculation but they're deterministic from messages
    orig_hash_coeffs, orig_m_coeffs = chameleon_hash_ring_lwe(
        a_coeffs, b_coeffs, original_message, r_coeffs, q, n, return_raw=True
    )
    
    _, mod_m_coeffs = chameleon_hash_ring_lwe(
        a_coeffs, b_coeffs, modified_message, r_coeffs, q, n, return_raw=True
    )
    
    # Initialize symbolic variable
    x = symbols('x')
    
    # Define polynomial modulus x^n + 1
    mod_poly = Poly([1] + [0] * (n-1) + [1], x, domain=GF(q))
    
    # Convert coefficient lists to polynomials
    a_poly = Poly(a_coeffs, x, domain=GF(q))
    b_poly = Poly(b_coeffs, x, domain=GF(q))
    r_poly = Poly(r_coeffs, x, domain=GF(q))
    orig_m_poly = Poly(orig_m_coeffs, x, domain=GF(q))
    mod_m_poly = Poly(mod_m_coeffs, x, domain=GF(q))
    
    # Get inverse of a
    try:
        inv_a_poly = invert(a_poly, mod_poly, domain=GF(q))
        inv_a_coeffs = extract_coeffs(inv_a_poly, n, q)
        print(f"  Inverted a first 5 coeffs: {inv_a_coeffs[:5]}")
    except Exception as e:
        print(f"[ERROR] Failed to invert polynomial a: {e}")
        return r_coeffs
    
    # Correct formula: r' = r + a^(-1) * b * (m - m')
    # where m and m' are the message polynomials
    
    # Calculate m - m'
    diff_poly = (orig_m_poly - mod_m_poly).rem(mod_poly)
    
    # Calculate b * (m - m')
    b_diff_poly = (b_poly * diff_poly).rem(mod_poly)
    
    # Calculate a^(-1) * b * (m - m')
    adjust_poly = (inv_a_poly * b_diff_poly).rem(mod_poly)
    
    # Calculate r' = r + a^(-1) * b * (m - m')
    r_prime_poly = (r_poly + adjust_poly).rem(mod_poly)
    r_prime_coeffs = extract_coeffs(r_prime_poly, n, q)
    
    print(f"  Original r first 5: {r_coeffs[:5]}")
    print(f"  New r' first 5: {r_prime_coeffs[:5]}")
    
    # Verify the collision by computing the hash with r'
    mod_hash_poly = ((a_poly * r_prime_poly) + (b_poly * mod_m_poly)).rem(mod_poly)
    mod_hash_coeffs = extract_coeffs(mod_hash_poly, n, q)
    
    # Check if hashes match
    hash_equal = np.array_equal(orig_hash_coeffs, mod_hash_coeffs)
    
    print("\n[DEBUG] Verifying hash polynomial collision:")
    print(f"  Original hash polynomial (first 10): {orig_hash_coeffs[:10]}")
    print(f"  Modified hash polynomial (first 10): {mod_hash_coeffs[:10]}")
    print(f"  Hash polynomials match: {hash_equal}")
    
    if not hash_equal:
        print("[ERROR] Hash polynomials don't match!")
    else:
        print("[SUCCESS] Found a valid collision in the polynomial hash!")
    
    # Check if SHA-256 hashes will match
    orig_hash_bytes = np.array(orig_hash_coeffs[:min(len(orig_hash_coeffs), 64)], dtype=np.int64).tobytes()
    mod_hash_bytes = np.array(mod_hash_coeffs[:min(len(mod_hash_coeffs), 64)], dtype=np.int64).tobytes()
    
    orig_final_hash = hashlib.sha256(orig_hash_bytes).hexdigest()
    mod_final_hash = hashlib.sha256(mod_hash_bytes).hexdigest()
    
    print(f"\n[DEBUG] Verifying final SHA-256 hashes:")
    print(f"  Original final hash: {orig_final_hash}")
    print(f"  Modified final hash: {mod_final_hash}")
    print(f"  Final hashes match: {orig_final_hash == mod_final_hash}")
    
    return r_prime_coeffs

def test_ring_lwe_chameleon():
    """Test the Ring-LWE chameleon hash implementation"""
    # Parameters
    n = 256
    error_bound = 2
    np.random.seed(42)  # For reproducibility
    
    print("Generating Ring-LWE keys...")
    a_coeffs, s_coeffs, b_coeffs, q, n = generate_ring_lwe_keys(n, error_bound)
    print(f"Generated Ring-LWE parameters with n={n}, q={q}, error_bound={error_bound}")
    
    # Generate random polynomial for randomness
    r_coeffs = np.random.randint(0, q, size=n).tolist()
    
    # Test messages
    original_message = "Original block data: Alice sends 5 coins to Bob"
    modified_message = "Modified block data: Alice sends 10 coins to Bob"
    
    # Hash original message
    print("\n[DEBUG] Computing original hash:")
    original_hash = chameleon_hash_ring_lwe(a_coeffs, b_coeffs, original_message, r_coeffs, q, n)
    print(f"Original message hash: {original_hash[:15]}...")
    
    # Find collision
    print("\nFinding collision for modified message...")
    new_r_coeffs = find_collision_ring_lwe(a_coeffs, s_coeffs, b_coeffs, q, n,
                                          original_message, modified_message, r_coeffs)
    
    # Verify collision using the regular hash function
    print("\n[DEBUG] Computing modified hash with collision randomness:")
    modified_hash = chameleon_hash_ring_lwe(a_coeffs, b_coeffs, modified_message, new_r_coeffs, q, n)
    
    # Final check
    print(f"\nFinal verification:")
    print(f"Original hash: {original_hash}")
    print(f"Modified hash: {modified_hash}")
    
    if original_hash == modified_hash:
        print(f"\nSUCCESS: Hashes match! Collision found successfully.")
    else:
        print(f"\nFAILURE: Hashes don't match. There's an issue with the collision mechanism.")
    
    return original_hash == modified_hash

if __name__ == "__main__":
    success = test_ring_lwe_chameleon()
    print(f"\nRing-LWE Chameleon Hash Test {'Successful' if success else 'Failed'}")
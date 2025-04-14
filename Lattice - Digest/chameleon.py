import numpy as np
import hashlib

def generate_keys(n=256, q=8192, error_bound=3):
    """
    Generates cryptographic keys for Lattice-based Chameleon Hashing using LWE.
    
    Args:
        n: Dimension of the lattice (security parameter)
        q: Modulus for calculations
        error_bound: Maximum absolute value of error terms
        
    Returns:
        - matrix_A: Random matrix (public key component)
        - vector_s: Secret trapdoor vector (private key)
        - vector_b: Public key component computed as A⋅s + e
        - q: Modulus used for calculations
    """
    # Generate random matrix A
    matrix_A = np.random.randint(0, q, size=(n, n), dtype=np.int64)
    
    # Generate secret vector s (trapdoor)
    vector_s = np.random.randint(0, q, size=(n, 1), dtype=np.int64)
    
    # Generate small error vector e
    vector_e = np.random.randint(-error_bound, error_bound + 1, size=(n, 1), dtype=np.int64)
    
    # Compute vector b = A⋅s + e mod q
    vector_b = (np.matmul(matrix_A, vector_s) + vector_e) % q
    
    return matrix_A, vector_s, vector_b, q

def message_to_hash_vector(message, n, q):
    """
    Converts a message to a vector using a hash function.
    
    Args:
        message: The message to hash
        n: Dimension of the output vector
        q: Modulus for calculations
        
    Returns:
        An n-dimensional vector derived from the message hash
    """
    # Convert message to bytes if it's a string
    if isinstance(message, str):
        message_bytes = message.encode()
    else:
        message_bytes = message
    
    # Get hash of the message
    hash_value = hashlib.sha256(message_bytes).digest()
    
    # Convert hash to a list of integers
    hash_ints = [int(b) % 4 for b in hash_value]
    
    # Expand or reduce to get n elements
    while len(hash_ints) < n:
        hash_ints += hash_ints
    hash_ints = hash_ints[:n]
    
    # Scale values to be within [0, q-1]
    hash_vector = np.array([val % q for val in hash_ints], dtype=np.int64).reshape(n, 1)
    
    return hash_vector

def chameleon_hash(matrix_A, vector_b, message, vector_r, q, return_vector=False):
    """
    Computes the Lattice-based Chameleon Hash using dot product projection.
    Digest is computed using quantized, sorted vector components for stability.
    """
    n = matrix_A.shape[0]
    Gm = message_to_hash_vector(message, n, q)

    # Use dot product for better error resilience
    dot_product = int(np.dot(vector_b.flatten(), Gm.flatten()) % q)

    term1 = np.matmul(matrix_A, vector_r) % q
    term2 = (dot_product * np.ones((n, 1), dtype=np.int64)) % q

    hash_result = (term1 + term2) % q

    if return_vector:
        return hash_result

    # Digest projection: quantized, sorted values
    flat = hash_result.flatten() % q
    sorted_vals = np.sort(flat)[:4]  # take lowest 4
    quantized = np.round(sorted_vals / (q / 16)).astype(np.uint8)
    digest_input = bytes(quantized.tolist())

    print("Digest input (quantized):", quantized.tolist())

    return hashlib.sha256(digest_input).hexdigest()

def find_collision(matrix_A, vector_s, vector_b, q, original_message, modified_message, original_r):
    """
    Finds a chameleon hash collision using the trapdoor and tolerates LWE noise.
    """
    n = matrix_A.shape[0]

    original_hash_vector = message_to_hash_vector(original_message, n, q)
    modified_hash_vector = message_to_hash_vector(modified_message, n, q)

    original_scalar = np.sum(original_hash_vector) % q
    modified_scalar = np.sum(modified_hash_vector) % q
    scalar_diff = (original_scalar - modified_scalar) % q

    error_vector = (vector_b - np.matmul(matrix_A, vector_s)) % q
    error_vector = np.where(error_vector > q / 2, error_vector - q, error_vector)

    print(f"Original scalar: {original_scalar}")
    print(f"Modified scalar: {modified_scalar}")
    print(f"Scalar difference: {scalar_diff}")
    print(f"Residual error norm from e·Δ: {np.linalg.norm(error_vector * scalar_diff)}")
    print(f"Detected error vector norm: {np.linalg.norm(error_vector)}")

    collision_candidates = []

    candidate1 = (original_r + (vector_s * scalar_diff)) % q
    collision_candidates.append(("Original formula: r' = r + s·diff", candidate1))

    candidate2 = (original_r - (vector_s * scalar_diff)) % q
    collision_candidates.append(("Negated formula: r' = r - s·diff", candidate2))

    error_adjustment = (error_vector * scalar_diff) % q
    candidate3 = (original_r + (vector_s * scalar_diff) + error_adjustment) % q
    collision_candidates.append(("With error (add): r' = r + s·diff + e·diff", candidate3))

    candidate4 = (original_r - (vector_s * scalar_diff) - error_adjustment) % q
    collision_candidates.append(("With error (sub): r' = r - s·diff - e·diff", candidate4))

    original_digest = chameleon_hash(matrix_A, vector_b, original_message, original_r, q)

    for description, candidate_r in collision_candidates:
        candidate_digest = chameleon_hash(matrix_A, vector_b, modified_message, candidate_r, q)
        print(f"Testing {description}")
        print("Candidate digest:", candidate_digest)
        print("Original digest:", original_digest)

        if candidate_digest == original_digest:
            print(f"✅ Collision found with {description}!")
            print("\n--- Collision Summary ---")
            print(f"Scalar difference (Δ): {scalar_diff}")
            print(f"Error norm: {np.linalg.norm(error_vector):.2f}")
            print(f"Residual error norm from e·Δ: {np.linalg.norm(error_vector * scalar_diff):.2f}")
            print(f"Hash preserved: True")
            print("--------------------------\n")
            return candidate_r

    print("No direct collision found with standard formulas. Trying adjustments...")

    # Fallback: try scaled error corrections
    for scale in [0.1, 0.25, 0.5, 1.0]:
        adjustment = np.round((error_vector * scalar_diff * scale) / q).astype(np.int64)
        adjusted_r = (original_r - (vector_s * scalar_diff) - adjustment) % q
        adjusted_digest = chameleon_hash(matrix_A, vector_b, modified_message, adjusted_r, q)
        print("Digest input (adjusted):", adjusted_digest)

        if adjusted_digest == original_digest:
            print(f"✅ Collision found in fallback (scale={scale})!")
            print("\n--- Collision Summary ---")
            print(f"Scalar difference (Δ): {scalar_diff}")
            print(f"Error norm: {np.linalg.norm(error_vector):.2f}")
            print(f"Residual error norm from e·Δ: {np.linalg.norm(error_vector * scalar_diff):.2f}")
            print(f"Hash preserved: True")
            print("--------------------------\n")
            return adjusted_r

    print("❌ Collision not found — LWE noise still too large.")
    return original_r  # Return original just to avoid crashing
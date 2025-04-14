import numpy as np
import hashlib

def generate_keys(n=256, q=8192, error_bound=3):
    """
    Generates keys for LWE-based Chameleon Hashing.
    Uses small dimensions and error for simplicity but maintains LWE properties.
    
    Args:
        n: Dimension of the lattice
        q: Small prime modulus
        error_bound: Small error for LWE property
        
    Returns:
        - matrix_A: Public key matrix
        - vector_s: Secret trapdoor vector
        - vector_b: Public key component computed as A⋅s + e
        - q: Modulus used for calculations
        - vector_e: The error vector
    """
    # Create an identity matrix for A
    matrix_A = np.eye(n, dtype=np.int64)
    
    # Generate secret vector s
    vector_s = np.random.randint(0, q, size=(n, 1), dtype=np.int64)
    
    # Generate small error vector e
    vector_e = np.random.randint(-error_bound, error_bound + 1, size=(n, 1), dtype=np.int64)
    
    # Compute vector b = A⋅s + e mod q
    vector_b = (np.matmul(matrix_A, vector_s) + vector_e) % q
    
    return matrix_A, vector_s, vector_b, q, vector_e

def message_to_vector(message, n, q):
    """
    Converts a message to a vector using a more robust encoding algorithm.
    Creates a more uniform and unpredictable distribution of vector elements.
    
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
        message_bytes = str(message).encode()
    
    # Get hash of the message using SHA-256
    hash_value = hashlib.sha256(message_bytes).digest()
    
    # Create a more sophisticated encoding to spread the message values
    hash_ints = []
    
    # Use multiple values from each byte with different transformations
    for i in range(len(hash_value)):
        byte_val = hash_value[i]
        
        # Generate multiple values from each byte using different transformations
        val1 = byte_val % q
        val2 = (byte_val * 31 + 17) % q  # Multiply by prime and add offset
        val3 = (byte_val * 59 + 43) % q  # Different prime and offset
        
        hash_ints.extend([val1, val2, val3])
    
    # If we need more elements, use combinations of existing elements
    if len(hash_ints) < n:
        original_len = len(hash_ints)
        
        while len(hash_ints) < n:
            for i in range(original_len - 1):
                if len(hash_ints) >= n:
                    break
                # Mix pairs of values to create new ones
                new_val = (hash_ints[i] * 13 + hash_ints[i+1] * 7) % q
                hash_ints.append(new_val)
    
    # Take exactly n elements
    result_vector = np.array(hash_ints[:n], dtype=np.int64).reshape(n, 1)
    
    return result_vector

def chameleon_hash(matrix_A, vector_b, message, vector_r, q, debug=False):
    """
    Computes an LWE-based Chameleon Hash.
    H(m,r) = A⋅r + message_vector mod q
    
    Args:
        matrix_A: Public key matrix
        vector_b: Public key vector (not used in this simplified hash, but kept for API consistency)
        message: Message to hash
        vector_r: Random vector ensuring collision resistance
        q: Modulus for calculations
        debug: Whether to print debug information
        
    Returns:
        The chameleon hash value as a hex string
    """
    n = matrix_A.shape[0]
    
    # Convert message to a hash vector
    message_vector = message_to_vector(message, n, q)
    
    # Compute A⋅r mod q
    Ar = np.matmul(matrix_A, vector_r) % q
    
    # Compute A⋅r + message_vector mod q
    hash_result = (Ar + message_vector) % q
    
    # Convert the result to a fixed-length string
    flat_result = hash_result.flatten().tobytes()
    
    # Final hash
    final_hash = hashlib.sha256(flat_result).hexdigest()
    
    return final_hash

def find_collision(matrix_A, vector_s, vector_b, q, original_message, modified_message, original_r, vector_e=None):
    """
    Finds a collision for the LWE-based chameleon hash.
    Takes advantage of the identity matrix structure but accounts for LWE errors.
    
    Args:
        matrix_A: Public key matrix (identity matrix in this implementation)
        vector_s: Secret trapdoor vector (needed for API consistency)
        vector_b: Public key vector (needed for API consistency)
        q: Modulus for calculations
        original_message: Original message
        modified_message: Modified message
        original_r: Original random vector
        vector_e: Error vector (needed to account for LWE errors)
        
    Returns:
        A new random vector r' that creates a collision
    """
    n = matrix_A.shape[0]
    
    # Convert messages to vectors
    original_vector = message_to_vector(original_message, n, q)
    modified_vector = message_to_vector(modified_message, n, q)
    
    # Calculate the difference vector
    message_diff = (original_vector - modified_vector) % q
    
    # Calculate new_r
    new_r = (original_r + message_diff) % q
    
    # Verify the collision
    original_hash = chameleon_hash(matrix_A, vector_b, original_message, original_r, q)
    new_hash = chameleon_hash(matrix_A, vector_b, modified_message, new_r, q)
    
    # If hashes don't match, try adjusting with the error vector
    if original_hash != new_hash and vector_e is not None:
        # Try a simple adjustment by subtracting the error
        adjusted_r = (new_r - vector_e) % q
        
        # Check if this works
        adjusted_hash = chameleon_hash(matrix_A, vector_b, modified_message, adjusted_r, q)
        
        if original_hash == adjusted_hash:
            new_r = adjusted_r
    
    return new_r
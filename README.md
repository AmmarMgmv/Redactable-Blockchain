# Redactable-Blockchain

Basic – Uses a simple chameleon hash function.

Lattice-Digest – This version creates the chameleon hash digest by rounding and sorting parts of the lattice output, making it more stable to small changes and easier to compare using a compact SHA-256 hash. However, this version simplifies the design to the point where it compromises security.

Lattice-Identity Matrix – A proof-of-concept version of a lattice-based chameleon hash that uses an identity matrix. The use of the identity matrix simplifies the math but also weakens the security.

Lattice-Ring LWE – An attempt at a lattice-based chameleon hash function using the Ring-LWE approach.

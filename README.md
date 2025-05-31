# Redactable-Blockchain

Basic version uses a simple chameleon hash function

Lattice-Digest - This version creates the chameleon hash digest by rounding and sorting parts of the lattice output, making it more stable to small changes and easier to compare using a compact SHA-256 hash. This version simplifies it too much to the point where it loses security

Lattice-Identitu Matrix - This version is a Proof of Concept version of a lattice based chameleon hash but we use an identity matrix. With this the security is lost because the math is simplified due to the identity matrix.

Lattice-Ring LWE - This version is an attempt at implementing a lattice based chameleon hash function using the Ring LWE approach

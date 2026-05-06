import numpy as np
import sys
import os

# Mock the FaceRecognitionService or import it if possible
# For simplicity, we'll implement the same logic here to verify the math

def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def test_similarity():
    # Identical vectors should have 100% match
    v1 = [1.0] * 128
    v2 = [1.0] * 128
    sim = cosine_similarity(v1, v2) * 100
    print(f"Identical vectors match: {sim:.2f}% (Expected: 100.00%)")
    
    # Orthogonal vectors should have 0% match
    v3 = [1.0, 0.0] * 64
    v4 = [0.0, 1.0] * 64
    sim = cosine_similarity(v3, v4) * 100
    print(f"Orthogonal vectors match: {sim:.2f}% (Expected: 0.00%)")
    
    # Slightly different vectors
    v5 = [1.0] * 128
    v6 = [1.0] * 127 + [0.9]
    sim = cosine_similarity(v5, v6) * 100
    print(f"Slightly different vectors match: {sim:.2f}% (Expected: >99%)")
    
    print("\nThreshold Check:")
    if sim >= 85.0:
        print("✅ PASSED: 85% threshold check")
    else:
        print("❌ FAILED: 85% threshold check")

if __name__ == "__main__":
    test_similarity()

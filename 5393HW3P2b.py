def synthesize_binary_probability(binary_fraction):
    """
    Synthesizes a stochastic circuit from a binary probability string
    using only a 0.5 source stream. 
    """
    # Clean the input (remove '0.' if present and any trailing '2')
    clean_bin = binary_fraction.replace('0.', '').replace('2', '')
    
    # Calculate the true decimal target for verification
    true_decimal = sum(int(bit) * (0.5 ** (i + 1)) for i, bit in enumerate(clean_bin))
    
    print(f"=== Synthesizing {binary_fraction} ===")
    print(f"True Decimal Target: {true_decimal:.7f}\n")
    
    # Read bits from right (LSB) to left (MSB)
    reversed_bits = list(reversed(clean_bin))
    
    # Initialize the circuit with the right-most bit (always 1 in these problems)
    first_bit = reversed_bits.pop(0)
    current_p = 0.5 if first_bit == '1' else 0.0
    print(f"Start (LSB = {first_bit}): Source = {current_p:.7f}")
    
    # Process the remaining bits
    for step, bit in enumerate(reversed_bits):
        if bit == '0':
            # A '0' means pass the signal through an AND gate with 0.5
            current_p = current_p * 0.5
            gate = "AND (0.5)"
        elif bit == '1':
            # A '1' means pass the signal through an OR gate with 0.5
            # Formula for OR: P(A or B) = P(A) + P(B) - P(A)*P(B)
            current_p = current_p + 0.5 - (current_p * 0.5)
            gate = "OR  (0.5)"
            
        print(f" Gate {step+1:02d} [{gate}] -> Output: {current_p:.7f}")
        
    print(f"\nFinal Circuit Output: {current_p:.7f}")
    print("Match Successful!" if abs(current_p - true_decimal) < 1e-9 else "Error in logic!")
    print("="*40 + "\n")

# ---------------------------------------------------------
# Run the Homework Problems
# ---------------------------------------------------------

problems = [
    "0.1011111",
    "0.1101111",
    "0.1010111"
]

for prob in problems:
    synthesize_binary_probability(prob)
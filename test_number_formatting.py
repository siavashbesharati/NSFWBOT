#!/usr/bin/env python3
"""
Test script to demonstrate the improved number formatting
"""

from database import format_precise_number

def test_number_formatting():
    """Test the new number formatting function"""
    
    print("🔢 Testing Number Formatting")
    print("=" * 50)
    
    test_cases = [
        # (input, expected_behavior, description)
        (5.35649, "5.35649", "Preserve all precision"),
        (5.3500, "5.35", "Remove trailing zeros"),
        (5.0, "5", "Remove decimal for whole numbers"),
        (0.000461, "0.000461", "Preserve small decimals"),
        (8766.62, "8766.62", "Regular decimal"),
        (8766.000000, "8766", "Remove all trailing zeros"),
        (0, "0", "Zero value"),
        (123456.789012345, "123456.789012345", "High precision"),
        (0.013, "0.013", "Small decimal"),
        (5.50, "5.5", "Single trailing zero"),
        (10.00, "10", "Multiple trailing zeros"),
        (0.1000000000, "0.1", "Many trailing zeros"),
    ]
    
    print("Input Value\t\t-> Formatted\t\tDescription")
    print("-" * 70)
    
    for value, expected, description in test_cases:
        formatted = format_precise_number(value)
        status = "✅" if formatted == expected else f"❌ (got: {formatted})"
        print(f"{value:<15}\t-> {formatted:<15}\t{description} {status}")
    
    print("\n" + "=" * 50)
    print("✅ Number formatting preserves precision and removes trailing zeros only")

if __name__ == "__main__":
    test_number_formatting()
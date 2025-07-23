"""
Test file to validate that perturbation works correctly for non-degenerate instances.
This file demonstrates how perturbation eliminates ties between subset valuations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import random_test_case, apply_perturbation, generate_goods
from src.player import Player
import random
import itertools

def generate_unperturbed_test_case(k):
    """
    Generate a test case with k goods and 4 players using random valuations.
    Does NOT apply perturbation - used for demonstrating perturbation effects.
    
    Args:
        k: Number of goods to generate
        
    Returns:
        tuple: (goods_list, players_list, None) where players_list contains 4 Player objects
    """
    goods = generate_goods(k)
    
    # Generate random valuations for 4 players
    values_p1 = {good: random.randint(1, 10) for good in goods}
    values_p2 = {good: random.randint(1, 10) for good in goods}
    values_p3 = {good: random.randint(1, 10) for good in goods}
    values_p4 = {good: random.randint(1, 10) for good in goods}
    
    players = [
        Player('P1', values_p1),
        Player('P2', values_p2),
        Player('P3', values_p3),
        Player('P4', values_p4)
    ]
    
    return goods, players, None

def calculate_subset_valuation(player, subset):
    """
    Calculate the total valuation of a subset of goods for a player.
    
    Args:
        player: Player object
        subset: List of goods
        
    Returns:
        float: Total valuation of the subset
    """
    return sum(player.valuation[good] for good in subset)

def find_ties_in_valuations(player, goods):
    """
    Find all pairs of different subsets that have the same valuation for a player.
    
    Args:
        player: Player object
        goods: List of all goods
        
    Returns:
        list: List of tuples (subset1, subset2, shared_value) representing ties
    """
    ties = []
    
    # Generate all possible subsets (excluding empty set for simplicity)
    all_subsets = []
    for r in range(1, len(goods) + 1):
        for subset in itertools.combinations(goods, r):
            all_subsets.append(list(subset))
    
    # Check for ties between different subsets
    for i, subset1 in enumerate(all_subsets):
        for j, subset2 in enumerate(all_subsets):
            if i < j:  # Avoid checking the same pair twice
                val1 = calculate_subset_valuation(player, subset1)
                val2 = calculate_subset_valuation(player, subset2)
                
                if abs(val1 - val2) < 1e-10:  # Consider very small differences as ties
                    ties.append((subset1, subset2, val1))
    
    return ties

def demonstrate_perturbation_effect():
    """
    Demonstrate how perturbation eliminates ties and creates non-degenerate instances.
    """
    print("=" * 80)
    print("PERTURBATION DEMONSTRATION FOR NON-DEGENERATE INSTANCES")
    print("=" * 80)
      # Generate a small test case to demonstrate clearly
    goods, original_players, _ = generate_unperturbed_test_case(4)
    print(f"\nGoods: {goods}")
    print(f"Number of players: {len(original_players)}")
    
    # Apply perturbation
    perturbed_players, epsilon = apply_perturbation(original_players, goods)
    
    print(f"\nPerturbation parameter ε = {epsilon:.12f}")
    print(f"Powers of 2 used: {[2**(i+1) for i in range(len(goods))]}")
    
    # Analyze each player
    for player_idx, (original_player, perturbed_player) in enumerate(zip(original_players, perturbed_players)):
        print(f"\n" + "="*60)
        print(f"PLAYER {original_player.name} ANALYSIS")
        print(f"="*60)
        
        # Show original valuations
        print(f"\nORIGINAL VALUATIONS:")
        for good in goods:
            print(f"  {good}: {original_player.valuation[good]}")
        
        # Show perturbed valuations
        print(f"\nPERTURBED VALUATIONS:")
        for j, good in enumerate(goods):
            original_val = original_player.valuation[good]
            perturbed_val = perturbed_player.valuation[good]
            perturbation_added = epsilon * (2 ** (j + 1))
            print(f"  {good}: {original_val} + {perturbation_added:.10f} = {perturbed_val:.10f}")
        
        # Find ties in original valuations (limited to small subsets for clarity)
        print(f"\nCHECKING FOR TIES IN SUBSET VALUATIONS:")
        print(f"(Checking subsets of size 1 and 2 for demonstration)")
        
        # Check ties in original valuations
        small_subsets = []
        # Single goods
        for good in goods:
            small_subsets.append([good])
        # Pairs of goods
        for pair in itertools.combinations(goods, 2):
            small_subsets.append(list(pair))
        
        original_ties = []
        perturbed_ties = []
        
        # Find ties in original and perturbed valuations
        for i, subset1 in enumerate(small_subsets):
            for j, subset2 in enumerate(small_subsets):
                if i < j:
                    # Original valuations
                    orig_val1 = calculate_subset_valuation(original_player, subset1)
                    orig_val2 = calculate_subset_valuation(original_player, subset2)
                    
                    # Perturbed valuations
                    pert_val1 = calculate_subset_valuation(perturbed_player, subset1)
                    pert_val2 = calculate_subset_valuation(perturbed_player, subset2)
                    
                    if abs(orig_val1 - orig_val2) < 1e-10:
                        original_ties.append((subset1, subset2, orig_val1))
                    
                    if abs(pert_val1 - pert_val2) < 1e-10:
                        perturbed_ties.append((subset1, subset2, pert_val1))
        
        print(f"\nORIGINAL TIES FOUND: {len(original_ties)}")
        for subset1, subset2, value in original_ties:
            print(f"  {subset1} ≈ {subset2} (both = {value})")
        
        print(f"\nPERTURBED TIES FOUND: {len(perturbed_ties)}")
        if perturbed_ties:
            for subset1, subset2, value in perturbed_ties:
                print(f"  {subset1} ≈ {subset2} (both ≈ {value:.10f})")
        else:
            print("  None! ✓ Instance is non-degenerate for this player")
        
        # Show some example subset valuations
        print(f"\nEXAMPLE SUBSET VALUATIONS:")
        example_subsets = small_subsets[:6]  # Show first 6 subsets
        for subset in example_subsets:
            orig_val = calculate_subset_valuation(original_player, subset)
            pert_val = calculate_subset_valuation(perturbed_player, subset)
            print(f"  {subset}: {orig_val} → {pert_val:.10f}")

def test_non_degeneracy_validation():
    """
    Test that the perturbation successfully creates non-degenerate instances.
    """
    print(f"\n" + "="*80)
    print("NON-DEGENERACY VALIDATION TEST")
    print("="*80)
    
    # Test with different numbers of goods
    for num_goods in [3, 4, 5]:
        print(f"\n--- Testing with {num_goods} goods ---")
        
        # Generate original and perturbed instances
        goods, original_players, _ = generate_unperturbed_test_case(num_goods)
        perturbed_players, epsilon = apply_perturbation(original_players, goods)
        
        print(f"Goods: {goods}")
        print(f"Epsilon: {epsilon:.12f}")
        
        for player_idx, (orig_player, pert_player) in enumerate(zip(original_players, perturbed_players)):
            # Check for ties in original instance
            orig_ties = find_ties_in_valuations(orig_player, goods)
            pert_ties = find_ties_in_valuations(pert_player, goods)
            
            print(f"Player {orig_player.name}:")
            print(f"  Original ties: {len(orig_ties)}")
            print(f"  Perturbed ties: {len(pert_ties)}")
            
            if len(pert_ties) == 0:
                print(f"  ✓ Non-degenerate after perturbation")
            else:
                print(f"  ⚠ Still has ties after perturbation")
                for subset1, subset2, value in pert_ties[:3]:  # Show first 3 ties
                    print(f"    {subset1} ≈ {subset2} (≈ {value:.10f})")

def main():
    """
    Run all perturbation tests and demonstrations.
    """
    print("PERTURBATION TESTING AND VALIDATION")
    print("This demonstrates how perturbation creates non-degenerate instances")
    print("for EFX algorithms with 4 players.")
    
    # Run demonstrations
    demonstrate_perturbation_effect()
    test_non_degeneracy_validation()
    
    print(f"\n" + "="*80)
    print("PERTURBATION TESTING COMPLETE")
    print("="*80)
    print("\nSummary:")
    print("- Perturbation adds unique 'fingerprints' to each good using powers of 2")
    print("- This ensures different subsets have different total valuations")
    print("- The epsilon is chosen small enough to not change preference orders")
    print("- Result: Non-degenerate instances suitable for EFX algorithms")

if __name__ == "__main__":
    main()
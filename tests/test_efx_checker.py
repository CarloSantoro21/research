"""
Tests to validate that AllocationChecker.check_EFX functions correctly.
Includes cases that are EFX and cases that are NOT EFX to validate functionality.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.allocation_model import Allocation
from src.allocation_checker import AllocationChecker
from src.player import Player

def create_test_players():
    """Create test players with known valuations"""
    # Simple valuations to make calculations clearer
    valuations_p1 = {'A': 5, 'B': 3, 'C': 1, 'D': 2}
    valuations_p2 = {'A': 2, 'B': 5, 'C': 3, 'D': 1}
    valuations_p3 = {'A': 1, 'B': 2, 'C': 5, 'D': 3}
    valuations_p4 = {'A': 3, 'B': 1, 'C': 2, 'D': 5}
    
    players = [
        Player('P1', valuations_p1),
        Player('P2', valuations_p2),
        Player('P3', valuations_p3),
        Player('P4', valuations_p4)
    ]
    
    return players

def test_case_1_efx_allocation():
    """Case 1: Allocation that IS EFX"""
    print("=" * 60)
    print("CASE 1: EFX ALLOCATION (Expected: True)")
    print("=" * 60)
    
    players = create_test_players()
    checker = AllocationChecker(players)
      # Create allocation where each player has their most preferred good
    allocation = Allocation()
    allocation.set_assignment('P1', ['A'])  # P1 values A at 5
    allocation.set_assignment('P2', ['B'])  # P2 values B at 5
    allocation.set_assignment('P3', ['C'])  # P3 values C at 5
    allocation.set_assignment('P4', ['D'])  # P4 values D at 5
    
    # Calculate utilities
    allocation.set_utility('P1', 5)
    allocation.set_utility('P2', 5)
    allocation.set_utility('P3', 5)
    allocation.set_utility('P4', 5)
    print("Assignment:")
    for player in players:
        goods = allocation.get_assignment(player.name)
        utility = allocation.get_utility(player.name)
        print(f"  {player.name}: {goods} (utility: {utility})")
    
    # Verify EFX
    is_efx = checker.check_EFX(allocation)
    print(f"\nResult: {'EFX' if is_efx else 'Not EFX'}")
    
    # Manual analysis
    print("\nManual analysis:")
    print("  Each player has their most preferred good (value 5)")
    print("  If any player removed any good from another's bundle,")
    print("  the remaining value would be 0, which is less than their current utility (5)")
    print("  Therefore, no envy after removing any good -> EFX")
    
    return is_efx

def test_case_2_efx_allocation():
    """Case 2: Another allocation that IS EFX"""
    print("\n" + "=" * 60)
    print("CASE 2: EFX ALLOCATION WITH UNEQUAL BUNDLES (Expected: False)")
    print("=" * 60)
    
    players = create_test_players()
    checker = AllocationChecker(players)
    
    # More complex allocation
    allocation = Allocation()
    allocation.set_assignment('P1', ['A', 'D'])  # P1: A(5) + D(2) = 7
    allocation.set_assignment('P2', ['B'])       # P2: B(5) = 5
    allocation.set_assignment('P3', ['C'])       # P3: C(5) = 5
    allocation.set_assignment('P4', [])          # P4: empty = 0
      # Calculate utilities
    allocation.set_utility('P1', 7)
    allocation.set_utility('P2', 5)
    allocation.set_utility('P3', 5)
    allocation.set_utility('P4', 0)
    
    print("Assignment:")
    for player in players:
        goods = allocation.get_assignment(player.name)
        utility = allocation.get_utility(player.name)
        print(f"  {player.name}: {goods} (utility: {utility})")
    
    # Verify EFX
    is_efx = checker.check_EFX(allocation)
    print(f"\nResult: {'EFX' if is_efx else 'Not EFX'}")
    
    # Manual analysis
    print("\nManual analysis of critical cases:")
    print("  P4 vs P1: P4 values {A,D} at 3+5=8, but P4 has 0")
    print("    If we remove A: P4 values {D} at 5 > 0, STILL ENVY")
    print("    If we remove D: P4 values {A} at 3 > 0, STILL ENVY")
    print("    THIS CASE MIGHT NOT BE EFX - let's see the actual result...")
    
    return is_efx

def test_case_3_non_efx_allocation():
    """Case 3: Allocation that is NOT EFX"""
    print("\n" + "=" * 60)
    print("CASE 3: NON-EFX ALLOCATION (Expected: False)")
    print("=" * 60)
    
    players = create_test_players()
    checker = AllocationChecker(players)
    
    # Create allocation with clear envy
    allocation = Allocation()
    allocation.set_assignment('P1', ['A', 'B', 'C'])  # P1: A(5) + B(3) + C(1) = 9
    allocation.set_assignment('P2', ['D'])            # P2: D(1) = 1
    allocation.set_assignment('P3', [])               # P3: empty = 0
    allocation.set_assignment('P4', [])               # P4: empty = 0
      # Calculate utilities
    allocation.set_utility('P1', 9)
    allocation.set_utility('P2', 1)
    allocation.set_utility('P3', 0)
    allocation.set_utility('P4', 0)
    
    print("Assignment:")
    for player in players:
        goods = allocation.get_assignment(player.name)
        utility = allocation.get_utility(player.name)
        print(f"  {player.name}: {goods} (utility: {utility})")
    
    # Verify EFX
    is_efx = checker.check_EFX(allocation)
    print(f"\nResult: {'EFX' if is_efx else 'Not EFX'}")
    
    # Manual analysis
    print("\nManual analysis:")
    print("  P3 vs P1: P3 values {A,B,C} at 1+2+5=8, but P3 has 0")
    print("    If we remove A: P3 values {B,C} at 2+5=7 > 0 -> ENVY")
    print("    If we remove B: P3 values {A,C} at 1+5=6 > 0 -> ENVY") 
    print("    If we remove C: P3 values {A,B} at 1+2=3 > 0 -> ENVY")
    print("    P3 envies P1 even after removing any good -> NOT EFX")
    
    return is_efx

def test_case_4_non_efx_allocation():
    """Case 4: Another allocation that is NOT EFX"""
    print("\n" + "=" * 60)
    print("CASE 4: NON-EFX ALLOCATION WITH BALANCED BUNDLES (Expected: False)")
    print("=" * 60)
    
    players = create_test_players()
    checker = AllocationChecker(players)
    
    # Allocation where there is subtle envy
    allocation = Allocation()
    allocation.set_assignment('P1', ['B'])       # P1: B(3) = 3
    allocation.set_assignment('P2', ['A', 'C'])  # P2: A(2) + C(3) = 5  
    allocation.set_assignment('P3', ['D'])       # P3: D(3) = 3
    allocation.set_assignment('P4', [])          # P4: empty = 0
      # Calculate utilities
    allocation.set_utility('P1', 3)
    allocation.set_utility('P2', 5)
    allocation.set_utility('P3', 3)
    allocation.set_utility('P4', 0)
    
    print("Assignment:")
    for player in players:
        goods = allocation.get_assignment(player.name)
        utility = allocation.get_utility(player.name)
        print(f"  {player.name}: {goods} (utility: {utility})")
    
    # Verify EFX
    is_efx = checker.check_EFX(allocation)
    print(f"\nResult: {'EFX' if is_efx else 'Not EFX'}")
    
    # Manual analysis
    print("\nManual analysis:")
    print("  P1 vs P2: P1 values {A,C} at 5+1=6, but P1 has 3")
    print("    If we remove A: P1 values {C} at 1 < 3 -> NO ENVY")
    print("    If we remove C: P1 values {A} at 5 > 3 -> YES ENVY")
    print("    There is at least one way to remove a good that leaves envy -> NOT EFX")
    
    return is_efx

def print_player_valuations():
    """Print player valuations for reference"""
    print("\n" + "=" * 60)
    print("PLAYER VALUATIONS (for reference)")
    print("=" * 60)
    
    players = create_test_players()
    
    print(f"{'Good':<6}", end="")
    for player in players:
        print(f"{player.name:>8}", end="")
    print()
    print("-" * (6 + 8 * len(players)))
    
    goods = ['A', 'B', 'C', 'D']
    for good in goods:
        print(f"{good:<6}", end="")
        for player in players:
            print(f"{player.valuation[good]:>8}", end="")
        print()

def run_all_tests():
    """Run all EFX checker tests"""
    print("TESTING EFX CHECKER - FUNCTIONALITY VALIDATION")
    print("=" * 80)
    
    # Show valuations for reference
    print_player_valuations()
    
    # Run test cases
    results = []
    results.append(("Case 1 (EFX)", test_case_1_efx_allocation(), True))
    results.append(("Case 2 (EFX)", test_case_2_efx_allocation(), False))
    results.append(("Case 3 (No EFX)", test_case_3_non_efx_allocation(), False))
    results.append(("Case 4 (No EFX)", test_case_4_non_efx_allocation(), False))
    
    # Results summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for case_name, actual_result, expected_result in results:
        status = "PASS" if actual_result == expected_result else "FAIL"
        print(f"{case_name:<30} | Expected: {expected_result:<5} | Actual: {actual_result:<5} | {status}")
        if actual_result != expected_result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("ALL TESTS PASSED - EFX CHECKER FUNCTIONS CORRECTLY")
    else:
        print("SOME TESTS FAILED - REVIEW EFX CHECKER IMPLEMENTATION")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()
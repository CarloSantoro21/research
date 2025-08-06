import time
from src.allocation_manager import AllocationManager
from src.allocation_checker import AllocationChecker
from src.allocation_finder import AllocationFinder

def run_tests(goods, players):
    """
    Run tests for EFX algorithm with 4 players.
    Tests algorithm that constructs allocations in real-time.
    
    Args:
        goods: List of goods
        players: List of 4 Player objects
        
    Returns:
        dict: Results from algorithm tested
    """
    # Validate we have 4 players
    if len(players) != 4:
        raise ValueError("Tests are designed for exactly 4 players")
    
    # Initialize our components for 4-player scenarios
    manager = AllocationManager(players, goods)
    checker = AllocationChecker(players)
    finder = AllocationFinder(manager, checker)
    
    results = {}

    print(f"\n==================================================")
    print(f"EFX Algorithm for 4 agents")
    print(f"==================================================")
        
    # EFX Algorithm
    start_time = time.time()
    algorithm_result, phase2_info = finder.find_efx_allocation_algorithm_1()
    end_time = time.time()
    time_algorithm = end_time - start_time
    
    print(f"Execution time: {time_algorithm:.6f} seconds")
    
    # Check if allocation is EFX
    is_efx = False
    if algorithm_result:
        is_efx = checker.check_EFX(algorithm_result)
        print(f"Is the allocation EFX? {'Yes' if is_efx else 'No'}")
        print(f"Allocation details:")
        _print_allocation_details(algorithm_result, players)
    else:
        print("EFX Algorithm: No EFX allocation found")
    
    # Store results with EFX and Phase 2 information
    results['algorithm'] = {
        'time': time_algorithm, 
        'allocation': algorithm_result,
        'is_efx': is_efx,
        'phase2_info': phase2_info
    }
    
    # Algorithm summary
    print("\n========== ALGORITHM SUMMARY ==========")
    print(f"{'Algorithm':<20} | {'Time (s)':<15} | {'Is EFX?':<8} | {'Found Allocation?':<17}")
    print("-" * 70)
    
    # Algorithm result
    is_efx = "Yes" if algorithm_result and checker.check_EFX(algorithm_result) else "No"
    found = "Yes" if algorithm_result else "No"
    print(f"{'EFX Algorithm':<20} | {time_algorithm:<15.6f} | {is_efx:<8} | {found:<17}")
    
    
    return results

def _print_allocation_details(allocation, players):
    """
    Helper function to print detailed allocation information.
    
    Args:
        allocation: Allocation object
        players: List of Player objects
    """
    print("  Assignments:")
    for player in players:
        goods = allocation.get_assignment(player.name)
        utility = allocation.get_utility(player.name)
        print(f"    {player.name}: {goods} (utility: {utility})")
    
    total_utility = sum(allocation.get_utility(p.name) for p in players)
    min_utility = min(allocation.get_utility(p.name) for p in players)
    max_utility = max(allocation.get_utility(p.name) for p in players)
    
    print(f"  Total utility: {total_utility}")
    print(f"  Min utility: {min_utility}, Max utility: {max_utility}")
    print(f"  Utility ratio (min/max): {min_utility/max_utility:.3f}" if max_utility > 0 else "  Utility ratio: N/A")
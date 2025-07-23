"""
Example of how an Allocation object looks
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.allocation_model import Allocation
from src.player import Player

def show_allocation_example():
    """Shows an example of how an Allocation object looks"""
    
    print("=" * 60)
    print("ALLOCATION OBJECT EXAMPLE")
    print("=" * 60)
    
    # Create an example allocation
    allocation = Allocation()
    
    # Assign goods to players
    allocation.set_assignment('P1', ['A', 'C'])
    allocation.set_assignment('P2', ['B'])
    allocation.set_assignment('P3', ['D', 'E'])
    allocation.set_assignment('P4', [])
    
    # Assign utilities
    allocation.set_utility('P1', 15.234)
    allocation.set_utility('P2', 8.567)
    allocation.set_utility('P3', 12.891)
    allocation.set_utility('P4', 0.0)
    
    print("Allocation object structure:")
    print(f"  assignments: {allocation.assignments}")
    print(f"  utilities: {allocation.utilities}")
    
    print("\nObject methods:")
    print(f"  allocation.get_assignment('P1'): {allocation.get_assignment('P1')}")
    print(f"  allocation.get_utility('P1'): {allocation.get_utility('P1')}")
    print(f"  allocation.get_min_utility(): {allocation.get_min_utility()}")
    print(f"  allocation.get_player_with_min_utility(): {allocation.get_player_with_min_utility()}")
    print(f"  allocation.get_bundle_size('P3'): {allocation.get_bundle_size('P3')}")
    
    print("\nConversion to dictionary:")
    dict_representation = allocation.to_dict()
    print(f"  allocation.to_dict(): {dict_representation}")
    
    print("\nReconstruction from dictionary:")
    reconstructed = Allocation.from_dict(dict_representation)
    print(f"  Reconstructed - assignments: {reconstructed.assignments}")
    print(f"  Reconstructed - utilities: {reconstructed.utilities}")
    
    print("\nDetail by player:")
    for player_name in ['P1', 'P2', 'P3', 'P4']:
        goods = allocation.get_assignment(player_name)
        utility = allocation.get_utility(player_name)
        bundle_size = allocation.get_bundle_size(player_name)
        print(f"  {player_name}: {goods} | utility={utility:.3f} | bundle_size={bundle_size}")

if __name__ == "__main__":
    show_allocation_example()

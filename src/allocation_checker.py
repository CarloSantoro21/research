class AllocationChecker:
    """
    This provides methods to check if allocations satisfy certain properties.
    Adapted for 4-player scenarios.
    """
    def __init__(self, players):
        """
        Initialize checker for 4 players.
        
        Args:
            players: List of 4 Player objects
        """
        if len(players) != 4:
            raise ValueError("This code is designed to work with exactly 4 players")
        
        self.players = players
    
    def check_EFX(self, allocation):
        """
        Check if an allocation is EFX (Envy-Free up to any item) for 4 players.
        
        Algorithm explanation:
        1. For each pair of players (i, j):
        2. Check if player i envies player j's bundle
        3. Player i envies player j if:
           - Player i's utility from their own bundle < 
           - Player i's valuation of player j's bundle MINUS any single item from j's bundle
        4. If any player envies another (even after removing any item), allocation is not EFX
        5. If no envy is found for any pair, allocation is EFX
        
        Args:
            allocation: Allocation object to check
            
        Returns:
            bool: True if allocation is EFX, False otherwise
        """
        
        # Check all pairs of players for envy
        for i, player_i in enumerate(self.players):
            for j, player_j in enumerate(self.players):
                if i == j:  # Skip checking player against themselves
                    continue
                
                # Get player i's current utility and player j's goods
                player_i_utility = allocation.get_utility(player_i.name)
                player_j_goods = allocation.get_assignment(player_j.name)
                
                # If player j has no goods, no envy possible
                if not player_j_goods:
                    continue
                
                # Check if player i envies player j after removing any single item
                # Player i should not envy player j's bundle minus any item
                envy_detected = True  # Assume envy until proven otherwise
                
                # For each item in player j's bundle, check if removing it eliminates envy
                for good_to_remove in player_j_goods:
                    # Calculate player i's valuation of player j's bundle minus this good
                    player_j_bundle_minus_good = [g for g in player_j_goods if g != good_to_remove]
                    player_i_valuation_of_reduced_bundle = sum(
                        player_i.get_valuation(g) for g in player_j_bundle_minus_good
                    )
                    
                    # If player i doesn't envy the reduced bundle, no EFX violation for this pair
                    if player_i_utility >= player_i_valuation_of_reduced_bundle:
                        envy_detected = False
                        break
                
                # If player i still envies player j after removing any single item, 
                # the allocation is not EFX
                if envy_detected:
                    return False
        
        # If no envy was detected for any pair, the allocation is EFX
        return True

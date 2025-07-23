from src.allocation_model import Allocation

class AllocationManager:
    def __init__(self, players, goods):
        """
        Initialize allocation manager for 4 players.
        
        Args:
            players: List of 4 Player objects
            goods: List of goods to be allocated
        """
        if len(players) != 4:
            raise ValueError("This code is designed to work with exactly 4 players")
        
        self.players = players
        self.goods = goods
    
    def calculate_utilities(self, allocation):
        """
        Calculates the utilities of each player for a given allocation.
        Modifies the allocation object in-place, updating the utilities.
        
        Args:
            allocation: Allocation object to calculate utilities for
        """
        for player in self.players:
            player_name = player.name
            player_goods = allocation.get_assignment(player_name)
            utility = sum(player.get_valuation(good) for good in player_goods)
            allocation.set_utility(player_name, utility)

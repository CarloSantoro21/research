class Allocation:
    """
    An instance of this class would represent a single allocation of goods between players.
    """
    def __init__(self, assignments=None, utilities=None):
        self.assignments = assignments or {} # Dictionary mapping player names to lists of goods
        self.utilities = utilities or {} # Dictionary mapping player names to utility values
    
    def get_assignment(self, player_name):
        return self.assignments.get(player_name, [])
    
    def get_utility(self, player_name):
        return self.utilities.get(player_name, 0)
    
    def set_assignment(self, player_name, goods):
        self.assignments[player_name] = goods
    
    def set_utility(self, player_name, utility):
        self.utilities[player_name] = utility
    
    def get_min_utility(self):
        if not self.utilities:
            return 0
        return min(self.utilities.values())
    
    def get_player_with_min_utility(self):
        if not self.utilities:
            return None
        min_utility = self.get_min_utility()
        for player, utility in self.utilities.items():
            if utility == min_utility:
                return player
        return None
    
    def get_bundle_size(self, player_name):
        return len(self.get_assignment(player_name))
    
    def to_dict(self):
        return {
            'assignments': self.assignments,
            'utilities': self.utilities
        }
    
    @classmethod
    def from_dict(cls, allocation_dict):
        if not allocation_dict:
            return None
        return cls(
            assignments=allocation_dict.get('assignments', {}),
            utilities=allocation_dict.get('utilities', {})
        )

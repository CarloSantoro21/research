import statistics

class Player:
    def __init__(self, name, valuation):
        self.name = name 
        self.valuation = valuation
        self.normalized_valuation = None
        self.std_deviation = None
    
    def normalize_valuations(self, target):
        """
        Normalize valuations so that the sum of all goods equals target.
        
        Args:
            target: Target value for the sum of all valuations (typically 1 for proportional normalization)
        """
        current_sum = sum(self.valuation.values())
        if current_sum == 0:
            # Handle edge case where all valuations are 0
            self.normalized_valuation = {good: target / len(self.valuation) for good in self.valuation}
        else:
            scaling_factor = target / current_sum
            self.normalized_valuation = {good: value * scaling_factor for good, value in self.valuation.items()}
        
        # Calculate standard deviation of normalized valuations
        normalized_values = list(self.normalized_valuation.values())
        self.std_deviation = statistics.stdev(normalized_values) if len(normalized_values) > 1 else 0.0
    
    def get_valuation(self, good):
        """Get valuation for a good (uses normalized if available, otherwise original)"""
        if self.normalized_valuation:
            return self.normalized_valuation[good]
        return self.valuation[good]
    
    def get_std_deviation(self):
        """Get standard deviation of normalized valuations"""
        return self.std_deviation if self.std_deviation is not None else 0.0
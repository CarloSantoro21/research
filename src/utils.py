import itertools
import random
from src.player import Player
from src.config import config

def generate_goods(k):
    goods = []
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    for size in range(1, k // 26 + 3):
        for combo in itertools.product(alphabet, repeat=size):
            goods.append(''.join(combo))
            if len(goods) >= k:
                return goods[:k]
    
    return goods

def calculate_epsilon_for_non_degeneracy(goods):
    """
    Calculate a sufficiently small epsilon to ensure non-degeneracy.
    
    Args:
        goods: List of goods
        
    Returns:
        float: Small epsilon value for perturbation
    """
    m = len(goods)
    base_epsilon = config.get('testing.perturbation.base_epsilon', 0.0001)
    epsilon = base_epsilon / (2 ** (m + 1))
    return epsilon

def apply_perturbation(players, goods, epsilon=None):
    """
    Apply perturbation to make the instance non-degenerate.
    For each player and each good, modify the valuation as:
    v'_i(g_j) = v_i(g_j) + epsilon * 2^j
    
    Args:
        players: List of Player objects
        goods: List of goods 
        epsilon: Small perturbation value (calculated automatically if None)
        
    Returns:
        tuple: (perturbed_players, epsilon_used)
    """
    if epsilon is None:
        epsilon = calculate_epsilon_for_non_degeneracy(goods)
    
    # Create new players with perturbed valuations
    perturbed_players = []
    
    for player in players:
        # Create new valuation dictionary with perturbation
        new_valuation = {}
        
        for j, good in enumerate(goods):
            # Apply perturbation: v'(g_j) = v(g_j) + epsilon * 2^(j+1)
            # Using j+1 to start with 2^1 instead of 2^0
            original_value = player.valuation[good]
            perturbation = epsilon * (2 ** (j + 1))
            new_valuation[good] = original_value + perturbation
        
        # Create new player with perturbed valuations
        perturbed_player = Player(player.name, new_valuation)
        perturbed_players.append(perturbed_player)
    
    return perturbed_players, epsilon

def random_test_case(k):
    """
    Generate a test case with k goods and 4 players using random valuations.
    Always applies perturbation for non-degeneracy.
    
    Args:
        k: Number of goods to generate
        
    Returns:
        tuple: (goods_list, players_list, epsilon_used) where players_list contains 4 Player objects
    """
    # Get valuation range from config
    val_min = config.get('testing.valuation_range.min', 1)
    val_max = config.get('testing.valuation_range.max', 10)
    
    goods = generate_goods(k)
    
    # Generate random valuations for 4 players
    values_p1 = {good: random.randint(val_min, val_max) for good in goods}
    values_p2 = {good: random.randint(val_min, val_max) for good in goods}
    values_p3 = {good: random.randint(val_min, val_max) for good in goods}
    values_p4 = {good: random.randint(val_min, val_max) for good in goods}
    
    original_players = [
        Player('P1', values_p1),
        Player('P2', values_p2),
        Player('P3', values_p3),
        Player('P4', values_p4)    ]
    
    # Always apply perturbation for non-degeneracy
    players, epsilon = apply_perturbation(original_players, goods)
    return goods, players, epsilon

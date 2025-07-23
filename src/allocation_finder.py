from src.allocation_model import Allocation
from src.config import config

class AllocationFinder:
    """
    Implementation of algorithm to find EFX allocations for 4 players.
    Algorithm constructs allocations in real-time rather than exhaustive generation.
    """
    def __init__(self, manager, checker):
        """
        Initialize allocation finder for 4 players.
        
        Args:
            manager: AllocationManager object
            checker: AllocationChecker object
        """
        if len(manager.players) != 4:
            raise ValueError("This code is designed to work with exactly 4 players")
        
        self.manager = manager
        self.checker = checker
        self.players = manager.players
        self.goods = manager.goods
        
    def _normalize_all_valuations(self):
        """
        Normalize all player valuations so that each player's total valuation sum equals 1.
        This converts valuations to proportions, ensuring fair comparison of standard deviations across players.
        """
        # Use fixed target from config for normalization to proportions
        target = config.get('algorithm.normalization.target', 1)
        
        print("NORMALIZATION OF VALUATIONS")
        print("-" * 30)
        print(f"Target for each player: {target} (proportional normalization)")
        
        # Normalize each player
        for player in self.players:
            original_sum = sum(player.valuation.values())
            player.normalize_valuations(target)
            print(f"{player.name}: {original_sum:.3f} -> {target} (std_dev: {player.get_std_deviation():.3f})")
        
        print()
    
    def find_efx_allocation_algorithm_1(self):
        """
        EFX algorithm for finding allocations with 4 players.
        Three-phase approach:
        Phase 1A: Initial Round Robin with standard deviation-based ordering
        Phase 1B: Champion Graph allocation for remaining goods
        Phase 2: Pairwise redistribution between envying players (if not EFX after Phase 1)
        
        Returns:
            tuple: (Allocation, phase2_info) where phase2_info contains execution details
        """
        print("Starting EFX Algorithm - Three Phase Approach")
        print("=" * 60)
        
        # Initialize Phase 2 tracking
        phase2_info = {
            'executed': False,
            'steps': 0,
            'improvements_found': False,
            'efx_achieved_in_phase2': False,
            'envy_reduction': 0.0,
            'initial_envy': 0.0,
            'final_envy': 0.0
        }
        
        # Normalize all player valuations first
        self._normalize_all_valuations()
        
        # Print initial value functions to analyze preferences
        self._print_value_functions()
        
        # PHASE 1A: Initial Round Robin with standard deviation-based ordering
        print("\nPHASE 1A: Initial Round Robin with Standard Deviation-Based Ordering")
        print("-" * 70)
        allocation_dict = self._initial_round_robin_with_consideration()
        allocation_obj = self._dict_to_allocation(allocation_dict)
        self._print_allocation_state(allocation_obj, "After Round Robin")
        
        # PHASE 1B: Champion Graph for remaining goods
        print("\nPHASE 1B: Champion Graph Allocation")
        print("-" * 35)
        remaining_goods = self._get_remaining_goods(allocation_dict)
        
        # Print value functions again to analyze remaining goods opportunities
        if remaining_goods:
            print(f"\nAnalyzing opportunities with remaining goods: {remaining_goods}")
            self._print_value_functions()
        
        for i, good in enumerate(remaining_goods):
            print(f"\nProcessing good {i+1}/{len(remaining_goods)}: {good}")
            allocation_dict = self._champion_graph_allocation(good, allocation_dict)
            allocation_obj = self._dict_to_allocation(allocation_dict)
            self._print_allocation_state(allocation_obj, f"After assigning {good}")
        
        print("\n" + "=" * 60)
        print("PHASE 1 COMPLETE - Final allocation:")
        final_allocation = self._dict_to_allocation(allocation_dict)
        
        # Print final value functions for analysis
        print("\nFINAL VALUE FUNCTIONS ANALYSIS:")
        self._print_value_functions()
        
        self._print_allocation_state(final_allocation, "Final")
        
        # Check if allocation is EFX after Phase 1
        is_efx_after_phase1 = self.checker.check_EFX(final_allocation)
        print(f"\nEFX Status after Phase 1: {'[+] EFX' if is_efx_after_phase1 else '[-] Not EFX'}")
        
        # PHASE 2: Cut-and-Choose redistribution (only if not EFX after Phase 1)
        if not is_efx_after_phase1:
            print("\nPHASE 2: Cut-and-Choose Redistribution Between Envying Players")
            print("-" * 65)
            
            # Track Phase 2 execution
            phase2_info['executed'] = True
            _, initial_envy, _ = self._calculate_envy_matrix(final_allocation)
            phase2_info['initial_envy'] = initial_envy
            
            try:
                improved_allocation, steps_executed = self._phase2_stepwise_redistribution(final_allocation)
                phase2_info['steps'] = steps_executed
                
                if improved_allocation:
                    final_allocation = improved_allocation
                    phase2_info['improvements_found'] = True
                    
                    # Calculate envy reduction
                    _, final_envy, _ = self._calculate_envy_matrix(final_allocation)
                    phase2_info['final_envy'] = final_envy
                    phase2_info['envy_reduction'] = initial_envy - final_envy
                    
                    self._print_allocation_state(final_allocation, "After Phase 2")
                    
                    # Check final EFX status
                    is_efx_final = self.checker.check_EFX(final_allocation)
                    phase2_info['efx_achieved_in_phase2'] = is_efx_final
                    print(f"\nFinal EFX Status: {'[+] EFX' if is_efx_final else '[-] Not EFX'}")
                else:
                    print("Phase 2: No improvements found")
                    phase2_info['final_envy'] = phase2_info['initial_envy']
            
            except RuntimeError as e:
                # Phase 2 failed - this is a failed test case
                print(f"\n[X] PHASE 2 FAILED: {str(e)}")
                phase2_info['improvements_found'] = False
                phase2_info['efx_achieved_in_phase2'] = False
                phase2_info['final_envy'] = phase2_info['initial_envy']
                phase2_info['envy_reduction'] = 0.0
                
                # This should be treated as a failed test
                raise RuntimeError(f"Algorithm failed in Phase 2: {str(e)}")
        
        return final_allocation, phase2_info
    
    def _initial_round_robin_with_consideration(self):
        """
        Phase 1A: Round Robin with consideration for following players.
        
        This implements an intelligent round-robin allocation where:
        1. Players are ordered by standard deviation (highest first) - players with more
           differentiated preferences pick first to maximize their advantage
        2. Each player considers their top N options (not just their best)
        3. For each option, the player evaluates the impact on future players
        4. The player may sacrifice some personal utility for the collective benefit
        5. Ties are broken using opportunity cost analysis for the next player
        
        The rationale is that players with high variance in valuations can afford to be
        considerate since they have strong preferences that will still be satisfied,
        while players with uniform valuations need to pick earlier to avoid getting
        poor allocations.
        
        Returns:
            dict: Initial allocation {player_name: [goods]}
        """
        allocation = {player.name: [] for player in self.players}
        available_goods = self.goods.copy()
        
        # Calculate standard deviations for ordering (highest std dev first)
        player_std_devs = []
        for player in self.players:
            std_dev = player.get_std_deviation()
            player_std_devs.append((player, std_dev))
        
        # Sort by standard deviation (descending - highest differentiation first)
        player_std_devs.sort(key=lambda x: x[1], reverse=True)
        ordered_players = [p[0] for p in player_std_devs]
        
        # Print ordering explanation
        print("Standard deviation-based ordering (higher std dev picks first):")
        for i, (player, std_dev) in enumerate(player_std_devs):
            print(f"  {i+1}. {player.name}: std_dev={std_dev:.3f}")
        print()
        
        # Consideration parameters from config
        MAX_SACRIFICE_THRESHOLD = config.get('algorithm.phase_1a.max_sacrifice_threshold', 0.2)
        TOP_OPTIONS_TO_CONSIDER = config.get('algorithm.phase_1a.top_options_to_consider', 3)
        
        print("Round Robin with CONSIDERATION")
        
        for turn, current_player in enumerate(ordered_players):
            if not available_goods:
                break
            
            # Get remaining players (who will pick after current player)
            remaining_players = ordered_players[turn + 1:]
            
            print(f"\n  Turn {turn+1}: {current_player.name}'s decision process:")
            
            # Get player's top options from available goods
            player_options = self._get_top_options(current_player, available_goods, TOP_OPTIONS_TO_CONSIDER)
            
            if len(remaining_players) == 0:
                # Last player - just pick the best option
                best_option = player_options[0]
                chosen_good = best_option['good']
                print(f"    Last player - picks best: {chosen_good} (value: {best_option['value']:.3f})")
            else:
                # Evaluate consideration for each option using absolute metrics
                best_choice = self._choose_with_consideration(
                    player_options, 
                    remaining_players, 
                    available_goods, 
                    MAX_SACRIFICE_THRESHOLD
                )
                chosen_good = best_choice['good']
                
                print(f"    Final choice: {chosen_good} (value: {best_choice['value']:.3f})")
                if best_choice.get('sacrifice_ratio', 0) > 0:
                    print(f"    Sacrifice: {best_choice['sacrifice_ratio']:.1%} for {best_choice['future_benefit']:.3f} benefit to others")
            
            # Assign the chosen good
            allocation[current_player.name].append(chosen_good)
            available_goods.remove(chosen_good)
        
        return allocation
    
    def _get_top_options(self, player, available_goods, top_n):
        """
        Get player's top N options from available goods.
        
        Args:
            player: Player object
            available_goods: List of available goods
            top_n: Number of top options to return
            
        Returns:
            list: List of dicts with 'good' and 'value' keys, sorted by value (descending)
        """
        options = []
        for good in available_goods:
            value = player.get_valuation(good)  # Use normalized valuation
            options.append({'good': good, 'value': value})
        
        # Sort by value (descending) and take top N
        options.sort(key=lambda x: x['value'], reverse=True)
        return options[:top_n]
    
    def _choose_with_consideration(self, player_options, remaining_players, available_goods, max_sacrifice_threshold):
        """
        Choose good considering impact on remaining players with intelligent tie-breaking.
        
        Args:
            player_options: List of player's top options
            remaining_players: Players who will choose after current player
            available_goods: Currently available goods
            max_sacrifice_threshold: Maximum sacrifice ratio (0.0 to 1.0)
            
        Returns:
            dict: Chosen option with consideration metrics
        """
        best_option = player_options[0]  # Player's most preferred
        best_value = best_option['value']
        
        print(f"    Top options: {[(opt['good'], opt['value']) for opt in player_options]}")
        
        best_choice = best_option.copy()
        best_score = 0  # Consideration score
        tied_options = []  # Store options with same consideration score

        # Tolerance for tie detection with normalized values (0-1 scale)
        TIE_TOLERANCE = config.get('algorithm.phase_1a.tie_tolerance', 0.001)

        # Evaluate each option
        for option in player_options:
            current_good = option['good']
            current_value = option['value']
            
            # Calculate personal sacrifice
            sacrifice = best_value - current_value
            sacrifice_ratio = sacrifice / best_value if best_value > 0 else 0
            
            # Skip if sacrifice is too high
            if sacrifice_ratio > max_sacrifice_threshold:
                print(f"      {current_good}: Too much sacrifice ({sacrifice_ratio:.1%}) - skipped")
                continue
            
            # Calculate benefit for remaining players
            remaining_goods_after_choice = [g for g in available_goods if g != current_good]
            benefit_score = self._calculate_future_benefit(remaining_players, remaining_goods_after_choice)
            
            # Calculate consideration score
            # Higher score = better choice considering others
            # Formula: benefit_to_others - sacrifice
            consideration_score = benefit_score - sacrifice
            
            print(f"      {current_good}: value={current_value:.3f}, sacrifice={sacrifice:.3f}, future_benefit={benefit_score:.3f}, score={consideration_score:.3f}")
            
            # Store option with metrics
            option_with_metrics = option.copy()
            option_with_metrics['sacrifice'] = sacrifice
            option_with_metrics['benefit'] = benefit_score
            option_with_metrics['consideration_score'] = consideration_score
            
            if consideration_score > best_score + TIE_TOLERANCE:
                # New best score - clear tied options and update best
                best_score = consideration_score
                best_choice = option_with_metrics
                tied_options = [option_with_metrics]
            elif abs(consideration_score - best_score) <= TIE_TOLERANCE and best_score > 0:
                # Tie detected - add to tied options only if we haven't already added it
                if option_with_metrics not in tied_options:
                    tied_options.append(option_with_metrics)
        
        # Handle ties with intelligent tie-breaking
        if len(tied_options) > 1:
            print(f"    Tie detected between {len(tied_options)} options with score ~{best_score:.3f}")
            best_choice = self._break_tie_with_opportunity_cost(tied_options, remaining_players, available_goods)
            print(f"    Tie-breaker chose: {best_choice['good']} (opportunity cost analysis)")
        
        return best_choice
    
    def _break_tie_with_opportunity_cost(self, tied_options, remaining_players, available_goods):
        """
        Break ties between options with same consideration score using opportunity cost analysis.
        
        Opportunity Cost Theory:
        When multiple options provide the same "consideration score", we choose the one
        that minimizes the opportunity cost for the next player. Opportunity cost is
        defined as: value_of_current_good - value_of_best_alternative_remaining
        
        Interpretation:
        - High positive opportunity cost = taking something the next player values much
          more than their alternatives (harmful to them)
        - Low/negative opportunity cost = taking something the next player values less
          than their alternatives (less harmful to them)
        
        Strategy: Choose the option with the LOWEST opportunity cost for the next player.
        This leaves them with relatively better alternatives, promoting overall fairness.
        
        Args:
            tied_options: List of options with tied consideration scores
            remaining_players: Players who will choose after current player
            available_goods: Currently available goods
            
        Returns:
            dict: Best option after tie-breaking
        """
        if not remaining_players:
            # No remaining players - just return first option
            return tied_options[0]
        
        next_player = remaining_players[0]  # Focus on immediate next player
        best_option = tied_options[0]
        lowest_opportunity_cost = float('inf')
        
        print(f"    Tie-breaking analysis for next player {next_player.name}:")
        
        for option in tied_options:
            current_good = option['good']
            
            # Calculate what goods would remain if we take this option
            remaining_after_choice = [g for g in available_goods if g != current_good]
            print(f"    If we take {current_good}, remaining: {remaining_after_choice}")

            if not remaining_after_choice:
                # No goods left - opportunity cost is negative of this good's value to next player
                # (they lose everything and get nothing)
                opportunity_cost = -next_player.get_valuation(current_good)
            else:
                # Calculate opportunity cost: value of this good vs best alternative left
                this_good_value = next_player.get_valuation(current_good)
                best_alternative_value = max(next_player.get_valuation(g) for g in remaining_after_choice)
                opportunity_cost = this_good_value - best_alternative_value

                print(f"    {current_good}: {next_player.name} values at {this_good_value:.3f}, best alternative {best_alternative_value:.3f}")
            
            print(f"      {current_good}: opportunity_cost={opportunity_cost:.3f} (next player values at {next_player.get_valuation(current_good):.3f})")
            
            # LOWER (more negative) opportunity cost is better - less harmful to next player
            # We're taking something they care less about relative to their remaining alternatives
            if opportunity_cost < lowest_opportunity_cost:
                lowest_opportunity_cost = opportunity_cost
                best_option = option
        
        print(f"    Chosen option has lowest opportunity cost: {lowest_opportunity_cost:.3f}")
        return best_option

    def _calculate_future_benefit(self, remaining_players, remaining_goods):
        """
        Calculate how much benefit remaining players would get from remaining goods.
        This helps measure the "consideration" impact of current choice.
        
        Args:
            remaining_players: Players who will choose after current
            remaining_goods: Goods that will remain after current choice
            
        Returns:
            float: Benefit score for future players
        """
        if not remaining_players or not remaining_goods:
            return 0.0
        
        total_benefit = 0.0
        
        # Simulate what would happen if remaining players pick optimally
        simulated_goods = remaining_goods.copy()
        
        for player in remaining_players:
            if not simulated_goods:
                break
            
            # Find best good for this player from remaining
            best_value = 0
            best_good = None
            
            for good in simulated_goods:
                value = player.get_valuation(good)
                if value > best_value:
                    best_value = value
                    best_good = good
            
            if best_good:
                total_benefit += best_value
                simulated_goods.remove(best_good)
        
        # Normalize by number of remaining players
        avg_benefit = total_benefit / len(remaining_players) if remaining_players else 0
        
        return avg_benefit
    
    def _get_remaining_goods(self, allocation):
        """
        Get list of goods not yet assigned in the allocation.
        
        Returns:
            list: Unassigned goods
        """
        assigned_goods = []
        for goods_list in allocation.values():
            assigned_goods.extend(goods_list)
        
        remaining = [good for good in self.goods if good not in assigned_goods]
        print(f"Remaining goods to assign: {remaining}")
        return remaining
    
    def _champion_graph_allocation(self, good, allocation):
        """
        Phase 1B: Use champion graph to assign a single good.
        
        Args:
            good: The good to assign
            allocation: Current allocation state
            
        Returns:
            dict: Updated allocation
        """
        # Build champion graph for this good
        champion_graph = self._build_champion_graph(good, allocation)
        print(f"    Champion graph: {champion_graph}")
        
        # Look for cycles
        cycles = self._find_all_cycles(champion_graph)
        
        if cycles:
            print(f"    Found cycles: {cycles}")
            # Choose cycle that most reduces envy
            best_cycle = self._choose_best_cycle(cycles, good, allocation)
            allocation = self._process_cycle(best_cycle, good, allocation)
        else:
            print(f"    No cycle found - using source assignment")
            allocation = self._assign_to_source(good, allocation, champion_graph)
        
        return allocation
    
    def _build_champion_graph(self, good, allocation):
        """
        Build champion graph for assigning a specific good.
        
        The champion graph is a key concept in EFX algorithms:
        - For each player j, we consider the bundle X_j U {good}
        - We find which other player would most benefit from having this bundle
        - That player becomes the "champion" of player j
        - This creates a directed graph: j -> champion(j)
        
        Cycles in this graph indicate beneficial trading opportunities:
        If A -> B -> C -> A, then A wants B's bundle+good, B wants C's bundle+good,
        and C wants A's bundle+good, creating a win-win-win redistribution.
        
        Args:
            good: Good to be assigned
            allocation: Current allocation
            
        Returns:
            dict: Champion graph {player: champion_of_that_player}
        """
        champion_graph = {}
        
        for target_player in self.players:
            target_name = target_player.name
            target_bundle = allocation[target_name] + [good]
            
            # Find who would most want this bundle (target_bundle)
            best_champion = None
            best_gain = -1
            best_current_utility = float('inf')
            
            for potential_champion in self.players:
                if potential_champion.name == target_name:
                    continue  # Can't be champion of your own bundle
                
                # Calculate gain if this player got target_bundle instead of their current
                current_bundle = allocation[potential_champion.name]
                current_value = sum(potential_champion.get_valuation(g) for g in current_bundle)
                target_value = sum(potential_champion.get_valuation(g) for g in target_bundle)
                
                gain = target_value - current_value
                
                # Champion selection: highest absolute gain, tie-break by lowest current utility
                if (gain > best_gain or 
                    (gain == best_gain and current_value < best_current_utility)):
                    best_gain = gain
                    best_champion = potential_champion
                    best_current_utility = current_value
            
            if best_champion and best_gain > 0:  # Only add edge if there's actual envy
                champion_graph[target_name] = best_champion.name
                print(f"      {best_champion.name} is champion of {target_name}'s bundle + {good} (gain: +{best_gain:.3f})")
        
        return champion_graph
    
    def _find_all_cycles(self, graph):
        """
        Find all cycles in the champion graph using DFS.
        
        Args:
            graph: Champion graph {node: next_node}
            
        Returns:
            list: List of cycles found
        """
        visited = set()
        all_cycles = []
        
        def dfs(node, path, rec_stack):
            if node in rec_stack:
                # Found cycle - extract it
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                return cycle
            
            if node in visited:
                return None
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in graph:
                result = dfs(graph[node], path, rec_stack.copy())
                if result:
                    return result
            
            path.pop()
            return None
        
        # Try starting DFS from each node
        for start_node in graph:
            if start_node not in visited:
                cycle = dfs(start_node, [], set())
                if cycle and cycle not in all_cycles:
                    all_cycles.append(cycle)
        
        return all_cycles
    
    def _choose_best_cycle(self, cycles, good, allocation):
        """
        Choose the cycle that most reduces envy from multiple cycles.
        
        Args:
            cycles: List of cycles
            good: Good to assign
            allocation: Current allocation
            
        Returns:
            list: Best cycle to process
        """
        if len(cycles) == 1:
            return cycles[0]
        
        best_cycle = cycles[0]
        best_envy_reduction = 0
        
        for cycle in cycles:
            envy_reduction = self._calculate_envy_reduction(cycle, good, allocation)
            if envy_reduction > best_envy_reduction:
                best_envy_reduction = envy_reduction
                best_cycle = cycle
        
        print(f"      Chose cycle {best_cycle} (envy reduction: {best_envy_reduction:.3f})")
        return best_cycle
    
    def _calculate_envy_reduction(self, cycle, good, allocation):
        """
        Calculate how much envy would be reduced by processing this cycle.
        
        Args:
            cycle: Cycle to evaluate
            good: Good to assign
            allocation: Current allocation
            
        Returns:
            float: Envy reduction score
        """
        total_gain = 0
        
        for i, player_name in enumerate(cycle):
            player = next(p for p in self.players if p.name == player_name)
            
            # Current bundle
            current_bundle = allocation[player_name]
            current_value = sum(player.get_valuation(g) for g in current_bundle)
            
            # Next player's bundle in cycle (what they would get)
            next_player_name = cycle[(i + 1) % len(cycle)]
            next_bundle = allocation[next_player_name].copy()
            
            # If this is first player in cycle, they also get the new good
            if i == 0:
                next_bundle.append(good)
            
            next_value = sum(player.get_valuation(g) for g in next_bundle)
            gain = next_value - current_value
            
            total_gain += max(0, gain)  # Only count positive gains
        
        return total_gain
    
    def _process_cycle(self, cycle, good, allocation):
        """
        Process a cycle in the champion graph intelligently.
        Evaluates ALL players in the cycle for direct assignment and compares with rotation.
        Chooses the strategy that minimizes total envy.
        
        Args:
            cycle: List of player names forming a cycle
            good: Good to assign
            allocation: Current allocation
            
        Returns:
            dict: Updated allocation
        """
        print(f"      Processing cycle: {' -> '.join(cycle + [cycle[0]])}")
        
        # Calculate current envy baseline
        current_allocation_obj = self._dict_to_allocation(allocation)
        _, current_envy, _ = self._calculate_envy_matrix(current_allocation_obj)
        print(f"      Current total envy: {current_envy:.3f}")
        
        # Strategy 1: Evaluate direct assignment to ALL players in the cycle
        # Use EFX-envy as primary criterion, regular envy as tie-breaker
        best_direct_efx_envy = float('inf')
        best_direct_envy = float('inf')
        best_direct_recipient = None
        best_direct_valuation = None
        tied_direct_candidates = []
        
        # Tolerance for tie detection with non-degenerate goods
        TIE_TOLERANCE = config.get('algorithm.phase_1b.tie_tolerance', 0.001)
        
        print(f"      Strategy 1: Testing direct assignment to each player in cycle")
        
        for player_name in cycle:
            player = next(p for p in self.players if p.name == player_name)
            valuation = player.get_valuation(good)
            
            # Test direct assignment to this player
            test_allocation = allocation.copy()
            for pname in test_allocation:
                test_allocation[pname] = allocation[pname].copy()
            test_allocation[player_name].append(good)
            
            test_allocation_obj = self._dict_to_allocation(test_allocation)
            _, test_efx_envy, _ = self._calculate_efx_envy_matrix(test_allocation_obj)
            _, test_envy, _ = self._calculate_envy_matrix(test_allocation_obj)
            
            print(f"        {player_name} (values {good} at {valuation:.3f}): EFX-envy={test_efx_envy:.3f}, regular envy={test_envy:.3f}")
            
            # Primary criterion: EFX-envy (lower is better)
            if test_efx_envy < best_direct_efx_envy - TIE_TOLERANCE:
                # Clear winner in EFX-envy - significantly better
                best_direct_efx_envy = test_efx_envy
                best_direct_envy = test_envy
                best_direct_recipient = player_name
                best_direct_valuation = valuation
                tied_direct_candidates = [player_name]
            elif abs(test_efx_envy - best_direct_efx_envy) <= TIE_TOLERANCE:
                # EFX-envy tie - use regular envy as tie-breaker
                if test_envy < best_direct_envy - TIE_TOLERANCE:
                    # Better regular envy breaks the EFX-envy tie
                    best_direct_efx_envy = test_efx_envy
                    best_direct_envy = test_envy
                    best_direct_recipient = player_name
                    best_direct_valuation = valuation
                    tied_direct_candidates = [player_name]
                elif abs(test_envy - best_direct_envy) <= TIE_TOLERANCE:
                    # Both EFX-envy and regular envy tied - add to candidates for further tie-breaking
                    if test_efx_envy < best_direct_efx_envy:
                        best_direct_efx_envy = test_efx_envy
                    if test_envy < best_direct_envy:
                        best_direct_envy = test_envy
                    
                    if player_name not in tied_direct_candidates:
                        tied_direct_candidates.append(player_name)
                    
                    # Include previous best if not already there
                    if len(tied_direct_candidates) == 1 and best_direct_recipient and best_direct_recipient not in tied_direct_candidates:
                        tied_direct_candidates.insert(0, best_direct_recipient)
                    
                    best_direct_recipient = player_name
                    best_direct_valuation = valuation

        # Handle ties with lexicographic order 
        if len(tied_direct_candidates) > 1:
            print(f"        EFX-envy and regular envy tie detected between {tied_direct_candidates} (within tolerance {TIE_TOLERANCE}) - using lexicographic order")
            best_direct_recipient = min(tied_direct_candidates)  # P1 < P2 < P3 < P4
            # Update valuation for the chosen recipient
            chosen_player = next(p for p in self.players if p.name == best_direct_recipient)
            best_direct_valuation = chosen_player.get_valuation(good)
            print(f"        Lexicographic tie-breaker chose: {best_direct_recipient}")
        
        print(f"      Best direct assignment: {best_direct_recipient} (values {good} at {best_direct_valuation:.3f}, EFX-envy: {best_direct_efx_envy:.3f}, regular envy: {best_direct_envy:.3f})")
        
        # Strategy 2: Test rotation (original strategy)
        print(f"      Strategy 2: Testing rotation")
        test_allocation_rotation = allocation.copy()
        for player_name in test_allocation_rotation:
            test_allocation_rotation[player_name] = allocation[player_name].copy()
        
        # Perform rotation for testing
        original_bundles = {}
        for player_name in cycle:
            original_bundles[player_name] = test_allocation_rotation[player_name].copy()
        
        for i in range(len(cycle)):
            current_player = cycle[i]
            next_player = cycle[(i + 1) % len(cycle)]
            test_allocation_rotation[current_player] = original_bundles[next_player].copy()
        
        # Add the new good to the first player in cycle
        recipient_rotation = cycle[0]
        test_allocation_rotation[recipient_rotation].append(good)
        
        test_allocation_rotation_obj = self._dict_to_allocation(test_allocation_rotation)
        _, rotation_efx_envy, _ = self._calculate_efx_envy_matrix(test_allocation_rotation_obj)
        _, rotation_envy, _ = self._calculate_envy_matrix(test_allocation_rotation_obj)
        
        print(f"      Rotation (assign to {recipient_rotation}): EFX-envy={rotation_efx_envy:.3f}, regular envy={rotation_envy:.3f}")
        
        # Choose the strategy that results in lowest EFX-envy, tie-break with regular envy
        strategies = [
            ("direct assignment", best_direct_efx_envy, best_direct_envy, "direct"),
            ("rotation", rotation_efx_envy, rotation_envy, "rotation")
        ]
        
        # Sort by EFX-envy first, then by regular envy
        strategies.sort(key=lambda x: (x[1], x[2]))
        best_strategy_name, best_efx_envy, best_regular_envy, best_strategy_type = strategies[0]
        
        print(f"      [+] Choosing {best_strategy_name}")
        print(f"        (lowest EFX-envy: {best_efx_envy:.3f}, regular envy: {best_regular_envy:.3f})")
        
        if best_strategy_type == "direct":
            allocation[best_direct_recipient].append(good)
            print(f"      Assigned {good} directly to {best_direct_recipient}")
        elif best_strategy_type == "rotation":
            # Perform the actual rotation
            original_bundles = {}
            for player_name in cycle:
                original_bundles[player_name] = allocation[player_name].copy()
            
            for i in range(len(cycle)):
                current_player = cycle[i]
                next_player = cycle[(i + 1) % len(cycle)]
                allocation[current_player] = original_bundles[next_player].copy()
            
            # Add the new good to the recipient
            allocation[recipient_rotation].append(good)
            print(f"      Assigned {good} to {recipient_rotation} and rotated bundles in cycle")
        
        return allocation
    
    def _assign_to_source(self, good, allocation, champion_graph):
        """
        When no cycle exists, assign the good to a source node or best choice.
        
        Args:
            good: Good to assign
            allocation: Current allocation  
            champion_graph: Champion graph
            
        Returns:
            dict: Updated allocation
        """
        # Find source nodes (players with no incoming edges)
        all_players = {player.name for player in self.players}
        targets = set(champion_graph.keys())  # Players who are targets of envy
        sources = all_players - targets  # Players who are not envied
        
        if sources:
            # Pick source with lowest current utility (tie-breaking)
            best_source = None
            lowest_utility = float('inf')
            
            for source in sources:
                current_utility = sum(
                    next(p for p in self.players if p.name == source).get_valuation(g) 
                    for g in allocation[source]
                )
                if current_utility < lowest_utility:
                    lowest_utility = current_utility
                    best_source = source
            
            recipient = best_source
            print(f"      Assigned {good} to source node {recipient} (lowest utility)")
        else:
            # No clear source - assign to player who values this good most
            best_recipient = None
            best_value = -1
            
            for player in self.players:
                if player.get_valuation(good) > best_value:
                    best_value = player.get_valuation(good)
                    best_recipient = player.name
            
            recipient = best_recipient
            print(f"      No source found - assigned {good} to {recipient} (highest valuation: {best_value:.3f})")
        
        allocation[recipient].append(good)
        
        return allocation
    
    def _print_allocation_state(self, allocation, phase):
        """
        Print current allocation state with utilities.
        
        Args:
            allocation: Allocation object
            phase: String describing the phase
        """
        print(f"\n{phase} Allocation:")
        total_utility = 0
        
        for player in self.players:
            player_goods = allocation.get_assignment(player.name)
            utility = allocation.get_utility(player.name)
            total_utility += utility
            print(f"  {player.name}: {player_goods} (utility: {utility:.3f})")
        
        print(f"  Total utility: {total_utility:.3f}")
        
        # Quick EFX check
        is_efx = self.checker.check_EFX(allocation)
        print(f"  EFX status: {'[+] EFX' if is_efx else '[-] Not EFX'}")

        self._print_envy_analysis(allocation, phase)
    
    def _dict_to_allocation(self, allocation_dict):
        """
        Convert dictionary allocation to Allocation object with calculated utilities.
        
        Args:
            allocation_dict: Dictionary {player_name: [goods]}
            
        Returns:
            Allocation: Allocation object with utilities calculated
        """
        allocation = Allocation()
        
        # Set assignments
        for player_name, goods in allocation_dict.items():
            allocation.set_assignment(player_name, goods)
        
        # Calculate and set utilities using the manager
        self.manager.calculate_utilities(allocation)
        
        return allocation
    
    def _calculate_envy_matrix(self, allocation):
        """
        Calculate the complete envy matrix for the allocation.
        
        Args:
            allocation: Allocation object
            
        Returns:
            tuple: (envy_matrix, total_envy, individual_envy_totals)
        """
        envy_matrix = {}
        individual_envy_totals = {}
        total_envy = 0.0
        
        for player_i in self.players:
            envy_matrix[player_i.name] = {}
            individual_envy_totals[player_i.name] = 0.0
            
            # Get player i's current bundle and utility
            player_i_bundle = allocation.get_assignment(player_i.name)
            player_i_utility = sum(player_i.get_valuation(good) for good in player_i_bundle)
            
            for player_j in self.players:
                if player_i.name == player_j.name:
                    envy_matrix[player_i.name][player_j.name] = 0.0
                    continue
                
                # Calculate envy(i, j) = max(0, v_i(X_j) - v_i(X_i))
                player_j_bundle = allocation.get_assignment(player_j.name)
                player_i_valuation_of_j_bundle = sum(player_i.get_valuation(good) for good in player_j_bundle)
                
                envy = max(0.0, player_i_valuation_of_j_bundle - player_i_utility)
                envy_matrix[player_i.name][player_j.name] = envy
                individual_envy_totals[player_i.name] += envy
                total_envy += envy
        
        return envy_matrix, total_envy, individual_envy_totals

    def _calculate_efx_envy_matrix(self, allocation):
        """
        Calculate the EFX-envy matrix for the allocation.
        
        EFX-envy is the envy that remains after applying the EFX condition 
        (removing the least valued item from the envied bundle).
        
        For player i envying player j:
        - Standard envy: max(0, v_i(X_j) - v_i(X_i))
        - EFX-envy: max(0, v_i(X_j \ {least_valued_item}) - v_i(X_i))
        
        When EFX-envy = 0 for all pairs, the allocation is EFX.
        
        Args:
            allocation: Allocation object
            
        Returns:
            tuple: (efx_envy_matrix, total_efx_envy, individual_efx_envy_totals)
        """
        efx_envy_matrix = {}
        individual_efx_envy_totals = {}
        total_efx_envy = 0.0
        
        for player_i in self.players:
            efx_envy_matrix[player_i.name] = {}
            individual_efx_envy_totals[player_i.name] = 0.0
            
            # Get player i's current bundle and utility
            player_i_bundle = allocation.get_assignment(player_i.name)
            player_i_utility = sum(player_i.get_valuation(good) for good in player_i_bundle)
            
            for player_j in self.players:
                if player_i.name == player_j.name:
                    efx_envy_matrix[player_i.name][player_j.name] = 0.0
                    continue
                
                # Get player j's bundle
                player_j_bundle = allocation.get_assignment(player_j.name)
                
                if not player_j_bundle:
                    # Empty bundle - no EFX-envy possible
                    efx_envy_matrix[player_i.name][player_j.name] = 0.0
                    continue
                
                # Calculate EFX-envy: envy after removing least valued item from j's bundle
                # Find the item in j's bundle that i values the LEAST
                least_valued_item = None
                least_value = float('inf')
                
                for good in player_j_bundle:
                    value = player_i.get_valuation(good)
                    if value < least_value:
                        least_value = value
                        least_valued_item = good
                
                # Calculate value of j's bundle after removing the least valued item (from i's perspective)
                reduced_bundle_value = sum(player_i.get_valuation(g) for g in player_j_bundle if g != least_valued_item)
                
                # EFX-envy = max(0, value_of_reduced_bundle - player_i_utility)
                efx_envy = max(0.0, reduced_bundle_value - player_i_utility)
                
                efx_envy_matrix[player_i.name][player_j.name] = efx_envy
                individual_efx_envy_totals[player_i.name] += efx_envy
                total_efx_envy += efx_envy
        
        return efx_envy_matrix, total_efx_envy, individual_efx_envy_totals

    def _print_value_functions(self):
        """
        Print the complete value function (valuation matrix) for all players.
        This helps visualize areas of opportunity and preferences.
        """
        print("\n" + "="*80)
        print("VALUE FUNCTIONS FOR ALL PLAYERS")
        print("="*80)
        
        # Print header
        print(f"{'Good':<8}", end="")
        for player in self.players:
            print(f"{player.name:>12}", end="")
        print()
        print("-" * (8 + 12 * len(self.players)))
        
        # Print valuations for each good
        for good in self.goods:
            print(f"{good:<8}", end="")
            for player in self.players:
                print(f"{player.get_valuation(good):>12.3f}", end="")
            print()
        
        print("-" * (8 + 12 * len(self.players)))
        
        # Print summary statistics
        print(f"\n{'PLAYER STATISTICS':<20}")
        print("-" * 50)
        
        for player in self.players:
            valuations = [player.get_valuation(good) for good in self.goods]
            avg_val = sum(valuations) / len(valuations)
            min_val = min(valuations)
            max_val = max(valuations)
            
            print(f"{player.name:<8}: Avg={avg_val:>6.3f}, Min={min_val:>6.3f}, Max={max_val:>6.3f}, Range={max_val-min_val:>6.3f}")

    def _print_envy_analysis(self, allocation, phase):
        """
        Print comprehensive envy analysis for the current allocation.
        
        Args:
            allocation: Allocation object
            phase: String describing the current phase
        """
        print(f"\n" + "="*80)
        print(f"ENVY ANALYSIS - {phase.upper()}")
        print("="*80)
        
        # Calculate envy matrix
        envy_matrix, total_envy, individual_envy_totals = self._calculate_envy_matrix(allocation)
        
        # Print envy matrix
        print(f"\nENVY MATRIX (envy(i,j) = max(0, v_i(X_j) - v_i(X_i))):")
        print("-" * 60)
        header = "Envier \\ Envied"
        print(f"{header:<15}", end="")
        for player in self.players:
            print(f"{player.name:>10}", end="")
        print(f"{'Total':>10}")
        print("-" * 60)
        
        for player_i in self.players:
            print(f"{player_i.name:<15}", end="")
            row_total = individual_envy_totals[player_i.name]
            
            for player_j in self.players:
                envy_val = envy_matrix[player_i.name][player_j.name]
                if envy_val == 0:
                    print(f"{'0.000':>10}", end="")
                else:
                    print(f"{envy_val:>10.3f}", end="")
            
            print(f"{row_total:>10.3f}")
        
        print("-" * 60)
        print(f"{'TOTAL SYSTEM ENVY':<15}{total_envy:>45.3f}")
        
        # Print individual envy analysis
        print(f"\nINDIVIDUAL ENVY BREAKDOWN:")
        print("-" * 40)
        
        for player_i in self.players:
            print(f"\n{player_i.name} envies:")
            player_total_envy = individual_envy_totals[player_i.name]
            
            if player_total_envy == 0:
                print(f"  -> No one! (Total envy: 0.000)")
            else:
                envies = []
                for player_j in self.players:
                    if player_i.name != player_j.name:
                        envy_val = envy_matrix[player_i.name][player_j.name]
                        if envy_val > 0:
                            envies.append((player_j.name, envy_val))
                
                # Sort by envy amount (descending)
                envies.sort(key=lambda x: x[1], reverse=True)
                
                for envied_player, envy_amount in envies:
                    percentage = (envy_amount / player_total_envy) * 100
                    print(f"  -> {envied_player}: {envy_amount:.3f} ({percentage:.1f}% of {player_i.name}'s total envy)")
                
                print(f"  -> Total envy by {player_i.name}: {player_total_envy:.3f}")
        
        # Print problem areas
        print(f"\nPROBLEM AREAS (High Envy Pairs):")
        print("-" * 40)
        
        high_envy_pairs = []
        for player_i in self.players:
            for player_j in self.players:
                if player_i.name != player_j.name:
                    envy_val = envy_matrix[player_i.name][player_j.name]
                    if envy_val > 0:
                        high_envy_pairs.append((player_i.name, player_j.name, envy_val))
        
        # Sort by envy amount (descending)
        high_envy_pairs.sort(key=lambda x: x[2], reverse=True)
        
        if not high_envy_pairs:
            print("  [+] No envy detected! Allocation is envy-free.")
        else:
            print("  Top envy sources:")
            for i, (envier, envied, envy_amount) in enumerate(high_envy_pairs[:5]):  # Top 5
                percentage = (envy_amount / total_envy) * 100
                print(f"  {i+1}. {envier} -> {envied}: {envy_amount:.3f} ({percentage:.1f}% of total envy)")
            
            if len(high_envy_pairs) > 5:
                print(f"  ... and {len(high_envy_pairs) - 5} more envy relationships")
        
        # Print EFX status
        is_efx = self.checker.check_EFX(allocation)
        print(f"\nEFX STATUS: {'[+] EFX SATISFIED' if is_efx else '[-] NOT EFX'}")
        
        if not is_efx and total_envy == 0:
            print("  Note: Zero envy but not EFX - this can happen with empty bundles or edge cases")
        
        # Print optimization suggestions
        if total_envy > 0:
            print(f"\nOPTIMIZATION OPPORTUNITIES:")
            print("-" * 30)
            
            # Find player with highest envy
            max_envy_player = max(individual_envy_totals.keys(), 
                                key=lambda p: individual_envy_totals[p])
            max_envy_amount = individual_envy_totals[max_envy_player]
            
            print(f"  * Focus on {max_envy_player} (highest total envy: {max_envy_amount:.3f})")
            
            # Find most envied player
            envy_received = {player.name: 0.0 for player in self.players}
            for player_i in self.players:
                for player_j in self.players:
                    if player_i.name != player_j.name:
                        envy_received[player_j.name] += envy_matrix[player_i.name][player_j.name]
            
            most_envied = max(envy_received.keys(), key=lambda p: envy_received[p])
            most_envied_amount = envy_received[most_envied]
            
            print(f"  * {most_envied} is most envied (receives {most_envied_amount:.3f} total envy)")
            print(f"  * Consider transferring goods from {most_envied} to {max_envy_player}")

    def _find_efx_division_for_envier(self, envier, all_goods):
        """
        Find a division of goods into two bundles that are EFX from the envier's perspective.
        
        Uses a split division algorithm that alternates goods between bundles
        to create relatively balanced bundles by value, which should produce EFX divisions.
        
        The envier needs to create two bundles such that they don't envy either bundle
        after removing any single item from it. This ensures that regardless of which
        bundle the other player chooses, the envier will be satisfied with their bundle.
        
        Args:
            envier: Player object (the one who will divide)
            all_goods: List of all goods to be divided
            
        Returns:
            tuple: (bundle_a, bundle_b) if EFX division found, None otherwise
        """
        if len(all_goods) < 2:
            return None
        
        print(f"        Finding EFX division for {envier.name} with goods: {all_goods}")
        
        # Try split division approach
        print(f"        Trying split division approach...")
        split_division = self._create_efx_bundles_split_division(envier, all_goods)
        
        if split_division and self._is_division_efx_for_player(envier, split_division[0], split_division[1]):
            print(f"        [+] Split division produced EFX division for {envier.name}")
            return split_division
        else:
            if split_division:
                print(f"        [-] Split division is NOT EFX for {envier.name}")
            else:
                print(f"        [-] Split division failed to create valid division")
            
            print(f"        EFX division failed for {envier.name}")
            return None
    
    def _create_efx_bundles_split_division(self, player, goods):
        """
        Create two bundles using a split division algorithm that alternates goods between bundles.
        
        Split Division Algorithm:
        1. Sort goods by player's valuation (descending)
        2. Start assigning to bundle1
        3. Switch to the other bundle when current bundle's value exceeds the other
        4. Continue until all goods are assigned
        
        This creates relatively balanced bundles by value, which should result in EFX divisions.
        
        Args:
            player: Player object whose valuations are used for balancing
            goods: List of goods to divide
            
        Returns:
            tuple: (bundle1, bundle2) or None if less than 2 goods
        """
        if len(goods) < 2:
            return None
        
        # Sort goods by player's valuation (descending - most valuable first)
        sorted_goods = sorted(goods, key=lambda g: player.get_valuation(g), reverse=True)
        
        bundle1 = []
        bundle2 = []
        current_bundle = 1  # Start with bundle1
        
        print(f"        Split division distribution (sorted by {player.name}'s valuations):")
        for good in sorted_goods:
            value = player.get_valuation(good)
            
            if current_bundle == 1:
                bundle1.append(good)
                value1 = sum(player.get_valuation(g) for g in bundle1)
                value2 = sum(player.get_valuation(g) for g in bundle2)
                print(f"          {good} -> Bundle1 (val={value:.3f}) | Bundle1={value1:.3f}, Bundle2={value2:.3f}")
                
                # Switch to bundle2 if bundle1 now has more value than bundle2
                if value1 > value2 and len(sorted_goods) > len(bundle1):  # Don't switch on last item
                    current_bundle = 2
                    print(f"          Switching to Bundle2 (Bundle1 exceeds Bundle2)")
            else:
                bundle2.append(good)
                value1 = sum(player.get_valuation(g) for g in bundle1)
                value2 = sum(player.get_valuation(g) for g in bundle2)
                print(f"          {good} -> Bundle2 (val={value:.3f}) | Bundle1={value1:.3f}, Bundle2={value2:.3f}")
                
                # Switch to bundle1 if bundle2 now has more value than bundle1
                if value2 > value1 and len(sorted_goods) > len(bundle1) + len(bundle2):  # Don't switch on last item
                    current_bundle = 1
                    print(f"          Switching to Bundle1 (Bundle2 exceeds Bundle1)")
        
        # Ensure both bundles are non-empty
        if not bundle1 or not bundle2:
            print(f"        Warning: One bundle is empty - redistributing")
            # Move one item from the non-empty bundle to the empty one
            if not bundle1 and bundle2:
                bundle1.append(bundle2.pop())
            elif not bundle2 and bundle1:
                bundle2.append(bundle1.pop())
        
        final_value1 = sum(player.get_valuation(g) for g in bundle1)
        final_value2 = sum(player.get_valuation(g) for g in bundle2)
        
        print(f"        Final split division result:")
        print(f"          Bundle1: {bundle1} (value={final_value1:.3f})")
        print(f"          Bundle2: {bundle2} (value={final_value2:.3f})")
        
        return (bundle1, bundle2)
    
    def _is_division_efx_for_player(self, player, bundle_a, bundle_b):
        """
        Check if a division into two bundles is EFX for a given player.
        
        A division is EFX for a player if they don't envy either bundle
        after removing any item from it.
        
        This means:
        1. If player has bundle_a, they don't envy bundle_b after removing any item from bundle_b
        2. If player has bundle_b, they don't envy bundle_a after removing any item from bundle_a
        
        Args:
            player: Player object
            bundle_a: First bundle (list of goods)
            bundle_b: Second bundle (list of goods)
            
        Returns:
            bool: True if division is EFX for the player
        """
        if not bundle_a or not bundle_b:
            return False
        
        # Calculate player's valuation of each bundle
        value_a = sum(player.get_valuation(g) for g in bundle_a)
        value_b = sum(player.get_valuation(g) for g in bundle_b)
        
        # Check EFX condition: player should not envy either bundle after removing any item
        
        # Scenario 1: Player has bundle_a, check if they envy bundle_b after removing any item from bundle_b
        for item_to_remove in bundle_b:
            reduced_bundle_b = [g for g in bundle_b if g != item_to_remove]
            value_reduced_b = sum(player.get_valuation(g) for g in reduced_bundle_b)
            
            if value_a < value_reduced_b:  # Player with bundle_a would envy reduced bundle_b
                return False
        
        # Scenario 2: Player has bundle_b, check if they envy bundle_a after removing any item from bundle_a
        for item_to_remove in bundle_a:
            reduced_bundle_a = [g for g in bundle_a if g != item_to_remove]
            value_reduced_a = sum(player.get_valuation(g) for g in reduced_bundle_a)
            
            if value_b < value_reduced_a:  # Player with bundle_b would envy reduced bundle_a
                return False
        
        return True

    def _phase2_stepwise_redistribution(self, allocation):
        """
        Phase 2: Stepwise cut-and-choose redistribution between envying players.
        Implements dynamic updates to envy relationships and detects cycles.
        Each step processes ONE envy relationship, then recalculates the list.
        """
        current_allocation = allocation
        step = 0

        # Initialize envy relationships (L) and seen states for cycle detection
        envy_relationships = self._get_envy_relationships(current_allocation)
        seen_states = set()

        # Calculate initial EFX-envy
        _, initial_efx_envy, _ = self._calculate_efx_envy_matrix(current_allocation)
        _, initial_regular_envy, _ = self._calculate_envy_matrix(current_allocation)
        
        print(f"Phase 2: Starting stepwise redistribution")
        print(f"  Initial EFX-envy: {initial_efx_envy:.3f}, Regular envy: {initial_regular_envy:.3f}")
        
        # Show comparison between regular envy and EFX-envy relationships
        regular_envy_matrix, _, _ = self._calculate_envy_matrix(current_allocation)
        regular_relationships = []
        for player_i in self.players:
            for player_j in self.players:
                if player_i.name != player_j.name and regular_envy_matrix[player_i.name][player_j.name] > 0:
                    regular_relationships.append((player_i.name, player_j.name))
        
        print(f"  Regular envy relationships: {regular_relationships}")
        print(f"  EFX-envy relationships: {envy_relationships}")

        while envy_relationships:
            step += 1
            print(f"\n--- Step {step} ---")
            print(f"  Current EFX-envy relationships in queue: {envy_relationships}")

            # Create comprehensive state hash that includes both envy relationships and goods context
            state_hash = self._create_phase2_state_hash(envy_relationships, current_allocation)
            if state_hash in seen_states:
                print(f"  [X] CYCLE DETECTED - same state seen before")
                raise RuntimeError("Cycle detected in Phase 2 - algorithm failed.")
            seen_states.add(state_hash)

            # Extract ONE envy relationship from the queue
            envier_name, envied_name = envy_relationships.pop(0)
            print(f"  Processing pair: {envier_name} (envier) -> {envied_name} (envied)")

            # Calculate current EFX-envy for comparison
            _, current_efx_envy, _ = self._calculate_efx_envy_matrix(current_allocation)
            _, current_regular_envy, _ = self._calculate_envy_matrix(current_allocation)
            print(f"  Current total EFX-envy: {current_efx_envy:.3f}, Regular envy: {current_regular_envy:.3f}")

            # Get player objects
            envier_obj = next(p for p in self.players if p.name == envier_name)
            envied_obj = next(p for p in self.players if p.name == envied_name)

            # Apply Cut-and-Choose
            all_goods = current_allocation.get_assignment(envier_name) + current_allocation.get_assignment(envied_name)
            
            if len(all_goods) < 2:
                print(f"    [X] Skipping - not enough goods to divide ({len(all_goods)} goods)")
                continue
                
            efx_division = self._find_efx_division_for_envier(envier_obj, all_goods)

            if not efx_division:
                print(f"    [X] Could not find EFX division for {envier_name}")
                continue

            bundle_a, bundle_b = efx_division

            # Step 2: Envied player chooses their preferred bundle
            envied_value_a = sum(envied_obj.get_valuation(g) for g in bundle_a)
            envied_value_b = sum(envied_obj.get_valuation(g) for g in bundle_b)

            if envied_value_a >= envied_value_b:
                envied_chosen = bundle_a
                envier_gets = bundle_b
            else:
                envied_chosen = bundle_b
                envier_gets = bundle_a

            print(f"    [>] Cut-and-Choose:")
            print(f"      Envier divided into: A={bundle_a}, B={bundle_b}")
            print(f"      {envied_name} values: A={envied_value_a:.3f}, B={envied_value_b:.3f}")
            print(f"      {envied_name} chose: {envied_chosen}")
            print(f"      {envier_name} gets: {envier_gets}")

            # Calculate new envy levels after redistribution
            test_allocation = Allocation()
            for player in self.players:
                if player.name == envier_name:
                    test_allocation.set_assignment(player.name, envier_gets)
                elif player.name == envied_name:
                    test_allocation.set_assignment(player.name, envied_chosen)
                else:
                    test_allocation.set_assignment(player.name, current_allocation.get_assignment(player.name))
            self.manager.calculate_utilities(test_allocation)

            _, new_efx_envy, _ = self._calculate_efx_envy_matrix(test_allocation)
            _, new_regular_envy, _ = self._calculate_envy_matrix(test_allocation)

            print(f"    [?] Evaluating redistribution:")
            print(f"      Current EFX-envy: {current_efx_envy:.3f} -> New EFX-envy: {new_efx_envy:.3f}")
            print(f"      Current regular envy: {current_regular_envy:.3f} -> New regular envy: {new_regular_envy:.3f}")

            # Apply redistribution only if it reduces total EFX-envy
            if new_efx_envy < current_efx_envy:
                print(f"    [+] Redistribution ACCEPTED - EFX-envy reduced by {current_efx_envy - new_efx_envy:.3f}")
                current_allocation = test_allocation

                # Recalculate envy relationships after this redistribution
                old_relationships = envy_relationships.copy()
                envy_relationships = self._get_envy_relationships(current_allocation)
                print(f"    [>] Updated EFX-envy relationships: {old_relationships} -> {envy_relationships}")
                
                # Reset seen states since we made progress
                seen_states = set()
            else:
                print(f"    [-] Redistribution REJECTED - does not reduce EFX-envy")
                print(f"      (would increase by {new_efx_envy - current_efx_envy:.3f})")

            # Print current step summary
            _, step_final_efx_envy, _ = self._calculate_efx_envy_matrix(current_allocation)
            _, step_final_regular_envy, _ = self._calculate_envy_matrix(current_allocation)
            print(f"  [*] Step {step} complete:")
            print(f"    Final EFX-envy: {step_final_efx_envy:.3f}, Regular envy: {step_final_regular_envy:.3f}")
            print(f"    Remaining relationships to process: {len(envy_relationships)}")

            # Check if EFX is achieved after this step
            if step_final_efx_envy == 0.0:
                print(f"\n[!] EFX ACHIEVED after {step} steps!")
                print(f"  Final EFX-envy: {step_final_efx_envy:.3f}, Final regular envy: {step_final_regular_envy:.3f}")
                print(f"  Improvement: EFX-envy {initial_efx_envy:.3f} -> {step_final_efx_envy:.3f} (-{initial_efx_envy - step_final_efx_envy:.3f})")
                print(f"  Early termination: EFX condition satisfied, no need to process remaining {len(envy_relationships)} relationships")
                return current_allocation, step

        # Final check for EFX-envy (only reached if loop completed without early termination)
        _, final_efx_envy, _ = self._calculate_efx_envy_matrix(current_allocation)
        _, final_regular_envy, _ = self._calculate_envy_matrix(current_allocation)
        
        if final_efx_envy == 0:
            print(f"\n[!] EFX ACHIEVED after {step} steps!")
            print(f"  Final EFX-envy: {final_efx_envy:.3f}, Final regular envy: {final_regular_envy:.3f}")
            print(f"  Improvement: EFX-envy {initial_efx_envy:.3f} -> {final_efx_envy:.3f} (-{initial_efx_envy - final_efx_envy:.3f})")
            return current_allocation, step
        else:
            raise RuntimeError(f"Phase 2 failed: No valid redistribution found and EFX-envy is not zero ({final_efx_envy:.3f}).")

    def _get_envy_relationships(self, allocation):
        """
        Calculate all EFX-envy relationships based on the current allocation.
        
        IMPORTANT: This uses EFX-envy instead of regular envy to ensure we target 
        the right relationships for Phase 2 redistribution.
        
        EFX-envy vs Regular envy:
        - Regular envy: envy(i,j) = max(0, v_i(X_j) - v_i(X_i))
        - EFX-envy: efx_envy(i,j) = max(0, v_i(X_j \ {least_valuable_good}) - v_i(X_i))
        
        Where X_j \ {least_valuable_good} means bundle of j excluding the good least valued by i.
        
        This is crucial because:
        1. Phase 2 aims to achieve EFX (not just envy-freeness)
        2. A player may have regular envy but no EFX-envy
        3. Processing only EFX-envy relationships is more efficient and targeted

        Args:
            allocation: Current allocation object

        Returns:
            list: List of tuples representing EFX-envy relationships (envier, envied)
        """
        envy_relationships = []
        efx_envy_matrix, _, _ = self._calculate_efx_envy_matrix(allocation)
        
        for player_i in self.players:
            for player_j in self.players:
                if player_i.name != player_j.name:
                    efx_envy = efx_envy_matrix[player_i.name][player_j.name]
                    if efx_envy > 0:
                        envy_relationships.append((player_i.name, player_j.name))

        return envy_relationships

    def _create_phase2_state_hash(self, envy_relationships, allocation):
        """
        Create a comprehensive hash for Phase 2 state that includes both 
        envy relationships and the specific goods context.
        
        This prevents false cycle detection when the same envy relationship
        exists but with different goods distributions.
        
        Args:
            envy_relationships: List of (envier, envied) tuples
            allocation: Current allocation object
            
        Returns:
            int: Hash representing the complete state
        """
        # Create state representation that includes:
        # 1. The envy relationships themselves
        # 2. The specific goods each player has
        state_components = []
        
        # Add envy relationships (order-independent)
        state_components.append(frozenset(envy_relationships))
        
        # Add goods distribution for each player involved in envy relationships
        involved_players = set()
        for envier, envied in envy_relationships:
            involved_players.add(envier)
            involved_players.add(envied)
        
        # Create sorted goods representation for each involved player
        for player_name in sorted(involved_players):
            player_goods = allocation.get_assignment(player_name)
            # Sort goods to make hash order-independent
            sorted_goods = tuple(sorted(player_goods))
            state_components.append((player_name, sorted_goods))
        
        # Create final hash from all components
        return hash(tuple(state_components))


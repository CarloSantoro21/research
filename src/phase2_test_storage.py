import json
import os
from datetime import datetime

class Phase2TestStorage:
    """
    Storage and management for test cases that enter Phase 2.
    Similar to            steps = phase2_info.get("steps", "N/A")
            improvements = "YES" if phase2_info.get("improvements_found", False) else "NO"
            efx_achieved = "YES" if phase2_info.get("efx_achieved_in_phase2", False) else "NO"
            
            phase2_details = f"Steps:{steps}, Imp:{improvements}, EFX:{efx_achieved}"edTestStorage but for Phase 2 execution tracking.
    """
    
    def __init__(self, filename="phase2_tests.json"):
        """
        Initialize Phase 2 test storage.
        
        Args:
            filename: JSON file to store Phase 2 test cases
        """
        self.filename = filename
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure the JSON file exists, create empty one if not."""
        if not os.path.exists(self.filename):
            self._save_data([])
    
    def _load_data(self):
        """Load Phase 2 test cases from JSON file."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data):
        """Save Phase 2 test cases to JSON file."""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_phase2_test(self, goods, players, test_mode, phase2_info=None):
        """
        Save a test case that entered Phase 2.
        
        Args:
            goods: List of goods in the test case
            players: List of Player objects
            test_mode: String describing the test mode ("single", "continuous", "manual")
            phase2_info: Dictionary with Phase 2 execution details
        """
        data = self._load_data()
        
        # Create test case entry
        test_case = {
            "id": len(data) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_mode": test_mode,
            "goods": goods,
            "players": [
                {
                    "name": player.name,
                    "valuations": player.valuation
                }
                for player in players
            ],
            "phase2_info": phase2_info or {}
        }
        
        data.append(test_case)
        self._save_data(data)
        
        print(f"Phase 2 test case saved (ID: {test_case['id']})")
    
    def get_phase2_tests_count(self):
        """Get the number of stored Phase 2 test cases."""
        data = self._load_data()
        return len(data)
    
    def get_phase2_test(self, test_id):
        """
        Get a specific Phase 2 test case by ID.
        
        Args:
            test_id: ID of the test case (1-indexed)
            
        Returns:
            dict: Test case data or None if not found
        """
        data = self._load_data()
        
        if 1 <= test_id <= len(data):
            return data[test_id - 1]
        else:
            return None
    
    def delete_phase2_test(self, test_id):
        """
        Delete a specific Phase 2 test case.
        
        Args:
            test_id: ID of the test case to delete (1-indexed)
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        data = self._load_data()
        
        if 1 <= test_id <= len(data):
            deleted_test = data.pop(test_id - 1)
            
            # Update IDs for remaining test cases
            for i, test in enumerate(data):
                test["id"] = i + 1
            
            self._save_data(data)
            print(f"Phase 2 test case {test_id} deleted successfully")
            return True
        else:
            print(f"Phase 2 test case {test_id} not found")
            return False
    
    def delete_multiple_phase2_tests(self, test_ids):
        """
        Delete multiple Phase 2 test cases.
        
        Args:
            test_ids: List of test IDs to delete (1-indexed)
            
        Returns:
            int: Number of test cases successfully deleted
        """
        data = self._load_data()
        deleted_count = 0
        
        # Sort in reverse order to avoid index shifting issues
        test_ids.sort(reverse=True)
        
        for test_id in test_ids:
            if 1 <= test_id <= len(data):
                data.pop(test_id - 1)
                deleted_count += 1
        
        # Update IDs for remaining test cases
        for i, test in enumerate(data):
            test["id"] = i + 1
        
        self._save_data(data)
        print(f"{deleted_count} Phase 2 test cases deleted successfully")
        return deleted_count
    
    def clear_all_phase2_tests(self):
        """Clear all Phase 2 test cases."""
        self._save_data([])
        print("All Phase 2 test cases cleared")
    
    def print_phase2_tests_summary(self):
        """Print a summary of all stored Phase 2 test cases."""
        data = self._load_data()
        
        if not data:
            print("No Phase 2 test cases stored.")
            return
        
        print(f"Stored Phase 2 test cases: {len(data)}")
        print()
        print("ID | Timestamp           | Mode       | Goods | Phase 2 Details")
        print("-" * 80)
        
        for test in data:
            goods_count = len(test["goods"])
            phase2_info = test.get("phase2_info", {})
            steps = phase2_info.get("steps", "N/A")
            improvements = "Yes" if phase2_info.get("improvements_found", False) else "No"
            efx_achieved = "Yes" if phase2_info.get("efx_achieved_in_phase2", False) else "No"
            
            phase2_details = f"Steps:{steps}, Imp:{improvements}, EFX:{efx_achieved}"
            
            print(f"{test['id']:2d} | {test['timestamp']} | {test['test_mode']:<10} | {goods_count:5d} | {phase2_details}")
    
    def print_phase2_test_details(self, test_id):
        """
        Print detailed information about a specific Phase 2 test case.
        
        Args:
            test_id: ID of the test case (1-indexed)
        """
        test = self.get_phase2_test(test_id)
        
        if not test:
            print(f"Phase 2 test case {test_id} not found")
            return
        
        print(f"PHASE 2 TEST CASE #{test['id']}")
        print("=" * 50)
        print(f"Timestamp: {test['timestamp']}")
        print(f"Test Mode: {test['test_mode']}")
        print(f"Number of goods: {len(test['goods'])}")
        print(f"Goods: {test['goods']}")
        print()
        
        # Phase 2 information
        phase2_info = test.get("phase2_info", {})
        if phase2_info:
            print("Phase 2 Execution Details:")
            print(f"  Steps: {phase2_info.get('steps', 'N/A')}")
            print(f"  Improvements found: {'Yes' if phase2_info.get('improvements_found', False) else 'No'}")
            print(f"  EFX achieved in Phase 2: {'Yes' if phase2_info.get('efx_achieved_in_phase2', False) else 'No'}")
            print(f"  Initial envy: {phase2_info.get('initial_envy', 'N/A')}")
            print(f"  Final envy: {phase2_info.get('final_envy', 'N/A')}")
            print(f"  Envy reduction: {phase2_info.get('envy_reduction', 'N/A')}")
        print()
        
        # Player valuations
        print("Player Valuations:")
        print("-" * 20)
        for player_data in test['players']:
            print(f"{player_data['name']}: {player_data['valuations']}")
        print()
    
    def get_all_phase2_tests(self):
        """Get all Phase 2 test cases."""
        return self._load_data()
    
    def recreate_players_from_test(self, test_id):
        """
        Recreate Player objects from a stored Phase 2 test case.
        
        Args:
            test_id: ID of the test case (1-indexed)
            
        Returns:
            tuple: (goods_list, players_list) or (None, None) if not found
        """
        from src.player import Player
        
        test = self.get_phase2_test(test_id)
        if not test:
            return None, None
        
        goods = test['goods']
        players = []
        
        for player_data in test['players']:
            player = Player(player_data['name'], player_data['valuations'])
            players.append(player)
        
        return goods, players
    
    def parse_indices_input(self, indices_input):
        """
        Parse user input for test case indices.
        Supports formats like: '1,3,5', '1 3 5', '1-5'
        
        Args:
            indices_input: String with indices
            
        Returns:
            list: List of integers (1-indexed)
        """
        indices = []
        
        # Replace commas with spaces and split
        parts = indices_input.replace(',', ' ').split()
        
        for part in parts:
            if '-' in part and len(part.split('-')) == 2:
                # Range format (e.g., "1-5")
                start, end = part.split('-')
                try:
                    start_num = int(start.strip())
                    end_num = int(end.strip())
                    indices.extend(range(start_num, end_num + 1))
                except ValueError:
                    raise ValueError(f"Invalid range format: {part}")
            else:
                # Single number
                try:
                    indices.append(int(part.strip()))
                except ValueError:
                    raise ValueError(f"Invalid number: {part}")
        
        return sorted(list(set(indices)))  # Remove duplicates and sort

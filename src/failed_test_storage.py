"""
System for storing and managing failed test cases.
Stores test cases that fail the EFX check for later re-testing.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class FailedTestStorage:
    """Manages storage and retrieval of failed test cases."""
    
    def __init__(self, storage_file: str = "failed_tests.json"):
        """
        Initialize failed test storage.
        
        Args:
            storage_file: Path to JSON file for storing failed tests
        """
        self.storage_file = storage_file
        self._ensure_storage_file_exists()
    
    def _ensure_storage_file_exists(self):
        """Create storage file if it doesn't exist."""
        if not os.path.exists(self.storage_file):
            self._save_data([])
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """Load failed tests from storage file."""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data: List[Dict[str, Any]]):
        """Save failed tests to storage file."""
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_failed_test(self, goods: List[str], players: List[Any], test_mode: str = "unknown"):
        """
        Save a failed test case.
        
        Args:
            goods: List of goods in the test case
            players: List of Player objects
            test_mode: Mode in which the test was run ("single", "continuous", etc.)
        """
        # Extract player valuations
        player_data = []
        for player in players:
            player_data.append({
                "name": player.name,
                "valuation": player.valuation
            })
        
        # Create test case entry
        test_case = {
            "timestamp": datetime.now().isoformat(),
            "test_mode": test_mode,
            "num_goods": len(goods),
            "goods": goods,
            "players": player_data
        }
        
        # Load existing data, add new test case, and save
        data = self._load_data()
        data.append(test_case)
        self._save_data(data)
        
        print(f"Failed test case saved (Test #{len(data)})")
    
    def get_all_failed_tests(self) -> List[Dict[str, Any]]:
        """Get all failed test cases."""
        return self._load_data()
    
    def get_failed_test_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific failed test by index (1-based).
        
        Args:
            index: 1-based index of the test case
            
        Returns:
            Test case dictionary or None if index is invalid
        """
        data = self._load_data()
        if 1 <= index <= len(data):
            return data[index - 1]
        return None
    
    def delete_failed_test(self, index: int) -> bool:
        """
        Delete a specific failed test by index (1-based).
        
        Args:
            index: 1-based index of the test case to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        data = self._load_data()
        if 1 <= index <= len(data):
            deleted_test = data.pop(index - 1)
            self._save_data(data)
            print(f"Deleted test case #{index} (from {deleted_test['timestamp']})")
            return True
        return False
    
    def delete_multiple_failed_tests(self, indices: List[int]) -> List[int]:
        """
        Delete multiple failed tests by indices (1-based).
        
        Args:
            indices: List of 1-based indices to delete
            
        Returns:
            List of indices that were successfully deleted
        """
        data = self._load_data()
        # Sort indices in descending order to avoid index shifting issues
        valid_indices = sorted([i for i in indices if 1 <= i <= len(data)], reverse=True)
        deleted_indices = []
        
        for index in valid_indices:
            deleted_test = data.pop(index - 1)
            deleted_indices.append(index)
            print(f"Deleted test case #{index} (from {deleted_test['timestamp']})")
        
        self._save_data(data)
        return sorted(deleted_indices)
    
    def clear_all_failed_tests(self) -> int:
        """
        Delete all failed test cases.
        
        Returns:
            Number of tests that were deleted
        """
        data = self._load_data()
        count = len(data)
        self._save_data([])
        print(f"Cleared all {count} failed test cases")
        return count
    
    def get_failed_tests_count(self) -> int:
        """Get the number of stored failed test cases."""
        return len(self._load_data())
    
    def print_failed_tests_summary(self):
        """Print a summary of all failed test cases."""
        data = self._load_data()
        
        if not data:
            print("No failed test cases stored.")
            return
        
        print(f"Stored failed test cases: {len(data)}")
        print()
        print("ID | Timestamp           | Mode       | Goods")
        print("-" * 55)
        
        for i, test_case in enumerate(data, 1):
            timestamp = test_case['timestamp']
            # Extract date and time from ISO format
            if 'T' in timestamp:
                date_time = timestamp.replace('T', ' ').split('.')[0]  # Remove microseconds
            else:
                date_time = timestamp
            
            mode = test_case['test_mode']
            num_goods = test_case['num_goods']
            
            print(f"{i:2d} | {date_time} | {mode:<10} | {num_goods:5d}")
    
    def print_failed_test_details(self, test_id):
        """
        Print detailed information about a specific failed test case.
        
        Args:
            test_id: ID of the test case (1-indexed)
        """
        test_case = self.get_failed_test_by_index(test_id)
        
        if not test_case:
            print(f"Failed test case {test_id} not found")
            return
        
        print(f"FAILED TEST CASE #{test_id}")
        print("=" * 50)
        print(f"Timestamp: {test_case['timestamp']}")
        print(f"Test Mode: {test_case['test_mode']}")
        print(f"Number of goods: {test_case['num_goods']}")
        print(f"Goods: {test_case['goods']}")
        print()
        
        # Player valuations
        print("Player Valuations:")
        print("-" * 20)
        for player_data in test_case['players']:
            print(f"{player_data['name']}: {player_data['valuation']}")
        print()
    
    def recreate_test_case(self, test_case: Dict[str, Any]):
        """
        Recreate Player objects and goods list from a stored test case.
        
        Args:
            test_case: Dictionary containing test case data
            
        Returns:
            tuple: (goods_list, players_list)
        """
        from src.player import Player
        
        goods = test_case['goods']
        players = []
        
        for player_data in test_case['players']:
            player = Player(player_data['name'], player_data['valuation'])
            players.append(player)
        
        return goods, players

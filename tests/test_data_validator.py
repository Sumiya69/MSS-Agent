"""
Test cases for the data validator agent.
"""
import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from agents.data_validator import DataValidator

class TestDataValidator(unittest.TestCase):
    """Test cases for DataValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        
        # Create temporary Excel files for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Valid data
        self.valid_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Amount': [100.0, 200.0, 300.0],
            'Status': ['Active', 'Active', 'Inactive']
        })
        
        # Invalid data with missing values
        self.invalid_data = pd.DataFrame({
            'ID': [1, 2, None],
            'Name': ['Alice', None, 'Charlie'],
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Amount': [100.0, 200.0, 300.0],
            'Status': ['Active', 'Active', None]
        })
        
        # Create test files
        self.valid_file = os.path.join(self.temp_dir, 'valid_data.xlsx')
        self.invalid_file = os.path.join(self.temp_dir, 'invalid_data.xlsx')
        
        self.valid_data.to_excel(self.valid_file, index=False)
        self.invalid_data.to_excel(self.invalid_file, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if os.path.exists(self.valid_file):
            os.remove(self.valid_file)
        if os.path.exists(self.invalid_file):
            os.remove(self.invalid_file)
        os.rmdir(self.temp_dir)
    
    def test_validate_valid_spreadsheet(self):
        """Test validation of a valid spreadsheet."""
        result = self.validator.validate_spreadsheet(self.valid_file)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['total_rows'], 3)
        self.assertEqual(result['total_columns'], 5)
        self.assertEqual(len(result['errors']), 0)
        self.assertFalse(result['missing_data_details']['has_missing_data'])
    
    def test_validate_invalid_spreadsheet(self):
        """Test validation of a spreadsheet with missing data."""
        result = self.validator.validate_spreadsheet(self.invalid_file)
        
        self.assertFalse(result['is_valid'])
        self.assertEqual(result['total_rows'], 3)
        self.assertTrue(result['missing_data_details']['has_missing_data'])
        self.assertGreater(len(result['missing_data_details']['missing_by_column']), 0)
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        result = self.validator.validate_spreadsheet('non_existent_file.xlsx')
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_missing_data_detection(self):
        """Test missing data detection functionality."""
        result = self.validator.validate_spreadsheet(self.invalid_file)
        missing_data = result['missing_data_details']
        
        self.assertTrue(missing_data['has_missing_data'])
        self.assertIn('ID', missing_data['missing_by_column'])
        self.assertIn('Name', missing_data['missing_by_column'])
        self.assertIn('Status', missing_data['missing_by_column'])
        self.assertGreater(missing_data['total_missing_values'], 0)

if __name__ == '__main__':
    unittest.main()

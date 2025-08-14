"""
Test cases for the Excel parser utility.
"""
import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from utils.excel_parser import ExcelParser

class TestExcelParser(unittest.TestCase):
    """Test cases for ExcelParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ExcelParser()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test data
        self.test_data = pd.DataFrame({
            'Column1': [1, 2, 3],
            'Column2': ['A', 'B', 'C'],
            'Column3': [10.5, 20.5, 30.5]
        })
        
        self.test_file = os.path.join(self.temp_dir, 'test_data.xlsx')
        self.test_data.to_excel(self.test_file, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def test_parse_excel_file(self):
        """Test parsing of Excel file."""
        df = self.parser.parse_excel_file(self.test_file)
        
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ['Column1', 'Column2', 'Column3'])
        self.assertEqual(df.iloc[0]['Column1'], 1)
        self.assertEqual(df.iloc[1]['Column2'], 'B')
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_excel_file('non_existent_file.xlsx')
    
    def test_unsupported_format(self):
        """Test handling of unsupported file format."""
        with self.assertRaises(ValueError):
            self.parser.parse_excel_file('test_file.txt')
    
    def test_validate_file_structure(self):
        """Test file structure validation."""
        df = self.parser.parse_excel_file(self.test_file)
        
        # Test with existing columns
        is_valid, missing = self.parser.validate_file_structure(df, ['Column1', 'Column2'])
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
        
        # Test with missing columns
        is_valid, missing = self.parser.validate_file_structure(df, ['Column1', 'MissingColumn'])
        self.assertFalse(is_valid)
        self.assertIn('MissingColumn', missing)
    
    def test_get_data_summary(self):
        """Test data summary generation."""
        df = self.parser.parse_excel_file(self.test_file)
        summary = self.parser.get_data_summary(df)
        
        self.assertEqual(summary['total_rows'], 3)
        self.assertEqual(summary['total_columns'], 3)
        self.assertEqual(summary['total_null_values'], 0)
        self.assertIn('Column1', summary['columns'])

if __name__ == '__main__':
    unittest.main()

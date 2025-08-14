"""
Script to create a sample Excel file for testing the data validation workflow.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def create_sample_excel():
    """Create a sample Excel file with some missing data for testing."""
    
    # Create sample data with some missing values
    data = {
        'ID': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Name': ['Alice', 'Bob', None, 'David', 'Eve', 'Frank', None, 'Helen', 'Ivan', 'Jane'],
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03', None, '2024-01-05', 
                '2024-01-06', '2024-01-07', '2024-01-08', None, '2024-01-10'],
        'Amount': [100.0, 200.0, 300.0, 400.0, None, 600.0, 700.0, 800.0, 900.0, None],
        'Status': ['Active', 'Active', 'Inactive', 'Active', 'Active', None, 'Active', 'Inactive', 'Active', 'Active']
    }
    
    df = pd.DataFrame(data)
    
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Save to Excel file
    output_path = data_dir / 'sample_master.xlsx'
    df.to_excel(output_path, index=False)
    
    print(f"Sample Excel file created: {output_path}")
    print(f"File contains {len(df)} rows with intentional missing data for testing")
    
    return output_path

if __name__ == "__main__":
    create_sample_excel()

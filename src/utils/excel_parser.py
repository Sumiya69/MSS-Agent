"""
Excel file parsing utilities.
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ExcelParser:
    """Handles Excel file parsing and data extraction."""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls']
    
    def parse_excel_file(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Parse Excel file and return DataFrame.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to read (default: first sheet)
            
        Returns:
            pandas.DataFrame: Parsed data
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            logger.info(f"Successfully parsed Excel file: {file_path}")
            logger.info(f"Data shape: {df.shape}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error parsing Excel file {file_path}: {str(e)}")
            raise
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Get all sheet names from Excel file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List[str]: List of sheet names
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error getting sheet names from {file_path}: {str(e)}")
            raise
    
    def validate_file_structure(self, df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate if DataFrame has required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, missing_columns)
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        is_valid = len(missing_columns) == 0
        
        if not is_valid:
            logger.warning(f"Missing required columns: {missing_columns}")
        
        return is_valid, missing_columns
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Get summary information about the DataFrame.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict: Summary information
        """
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'null_count_by_column': df.isnull().sum().to_dict(),
            'total_null_values': df.isnull().sum().sum(),
            'data_types': df.dtypes.astype(str).to_dict()
        }

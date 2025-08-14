"""
Data validation agent for Excel spreadsheets.
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

from utils.config import config
from utils.excel_parser import ExcelParser

logger = logging.getLogger(__name__)

class DataValidator:
    """Agent responsible for validating data in Excel spreadsheets."""
    
    def __init__(self):
        self.parser = ExcelParser()
        self.validation_config = config.validation_config
        self.required_columns = self.validation_config.get('required_columns', [])
        self.non_nullable_columns = self.validation_config.get('non_nullable_columns', [])
        self.product_schedule = getattr(config, 'product_schedule', {})
    
    def validate_spreadsheet(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, any]:
        """
        Enhanced validation: Full row validation with frequency-based logic.
        Validates entire row, not just specific columns. Skips quarterly/half-yearly columns.
        Auto-fetches rank_threshold from rules.
        """
        logger.info(f"Starting validation for file: {file_path}")
        
        try:
            # Parse the Excel file
            df = self.parser.parse_excel_file(file_path, sheet_name)

            # Get rank threshold from validation rules
            rank_threshold = self.validation_config.get('rules', {}).get('rank_threshold', 5)
            
            # Columns to skip during validation (quarterly/half-yearly)
            skip_columns = self.validation_config.get('skip_columns', [
                'q1', 'q2', 'q3', 'q4', 'h1', 'h2', 'quarterly', 'half_yearly', 'half-yearly'
            ])
            
            # Filter out columns to skip
            validation_columns = [col for col in df.columns if not any(skip.lower() in str(col).lower() for skip in skip_columns)]
            
            # Identify special column types
            percentage_columns = [col for col in validation_columns if '%' in str(col) or 'percent' in str(col).lower()]
            rank_columns = [col for col in validation_columns if 'rank' in str(col).lower()]
            
            # Find frequency column
            freq_col = None
            for col in df.columns:
                if 'frequency' in str(col).lower():
                    freq_col = col
                    break
            
            # Full row validation for each row
            product_issue_results = []
            
            for idx, row in df.iterrows():
                # Initialize validation status
                row_status = 'valid'
                row_details = []
                missing_values = []
                invalid_values = []
                
                # Check frequency-based validation skip
                should_validate = True
                frequency_value = None
                if freq_col and freq_col in row.index:
                    frequency_value = row[freq_col]
                    if frequency_value and str(frequency_value).lower() in ['quarterly', 'half-yearly', 'half_yearly']:
                        should_validate = False
                        row_status = 'skipped'
                        row_details.append(f"Skipped due to frequency: {str(frequency_value)}")

                if should_validate:
                    # Check all validation columns in the row
                    for col in validation_columns:
                        if col in row.index:
                            value = row[col]
                            
                            # Check for missing/null values
                            if pd.isnull(value) or (isinstance(value, str) and value.strip() == ''):
                                missing_values.append(str(col))
                            
                            # For percentage columns: only check for missing values (already handled above)
                            elif col in percentage_columns:
                                pass  # Only missing value check needed
                            
                            # For rank columns: check threshold
                            elif col in rank_columns and isinstance(value, (int, float)):
                                if value > rank_threshold:
                                    invalid_values.append(f"{str(col)}: {str(value)} exceeds rank threshold ({rank_threshold})")
                            
                            # For Outcome Number: check if it's a valid number
                            elif 'outcome number' in str(col).lower() and not pd.isnull(value):
                                try:
                                    float(str(value))
                                except (ValueError, TypeError):
                                    invalid_values.append(f"{str(col)}: '{str(value)}' is not a valid number")

                    # Determine row status based on validation results
                    if missing_values:
                        row_status = 'missing'
                        row_details.append(f"Missing values in: {', '.join([str(mv) for mv in missing_values])}")
                    
                    if invalid_values:
                        if row_status == 'valid':
                            row_status = 'invalid'
                        row_details.extend([str(iv) for iv in invalid_values])

                # Store results for this row
                product_issue_results.append({
                    'row_index': idx + 1,  # 1-based indexing for user display
                    'status': row_status,
                    'details': '; '.join([str(detail) for detail in row_details]) if row_details else 'All validations passed',
                    'missing_columns': [str(mv) for mv in missing_values],
                    'invalid_values': [str(iv) for iv in invalid_values],
                    'validation_columns_checked': len(validation_columns),
                    'frequency_info': frequency_value
                })

            # Calculate summary
            total_rows = len(df)
            valid_rows = len([r for r in product_issue_results if r['status'] == 'valid'])
            error_rows = len([r for r in product_issue_results if r['status'] != 'valid'])
            
            summary = {
                'total_rows': total_rows,
                'valid_rows': valid_rows,
                'error_rows': error_rows,
                'validation_rate': (valid_rows / total_rows * 100) if total_rows > 0 else 0,
                'total_columns': len(df.columns),
                'validation_columns': len(validation_columns),
                'skipped_columns': [str(col) for col in df.columns if col not in validation_columns],
                'columns': [str(col) for col in df.columns],
                'rank_threshold_used': rank_threshold
            }

            # Check for missing data using existing method
            missing_data_details = self._check_missing_data(df)

            return {
                'file_path': file_path,
                'sheet_name': sheet_name,
                'validation_timestamp': datetime.now().isoformat(),
                'is_valid': all(r['status'] == 'valid' for r in product_issue_results),
                'errors': [r for r in product_issue_results if r['status'] in ['error', 'invalid']],
                'warnings': [r for r in product_issue_results if r['status'] == 'missing'],
                'missing_data_details': missing_data_details,
                'summary': summary,
                'product_issue_results': product_issue_results,
                'validation_metadata': {
                    'full_row_validation': True,
                    'columns_validated': [str(col) for col in validation_columns],
                    'columns_skipped': summary['skipped_columns'],
                    'rank_threshold': rank_threshold
                }
            }

        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            return {
                'file_path': file_path,
                'validation_timestamp': datetime.now().isoformat(),
                'is_valid': False,
                'errors': [{'type': 'validation_error', 'message': str(e)}],
                'warnings': [],
                'missing_data_details': {},
                'summary': {}
            }
    
    def _check_missing_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Check for missing data in the DataFrame.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Dict with missing data details
        """
        missing_data_result = {
            'has_missing_data': False,
            'missing_rows': [],
            'missing_by_column': {},
            'total_missing_values': 0
        }
        
        # Check for completely empty rows
        empty_rows = df[df.isnull().all(axis=1)]
        if not empty_rows.empty:
            missing_data_result['has_missing_data'] = True
            missing_data_result['missing_rows'].extend(empty_rows.index.tolist())
        
        # Check for missing values in non-nullable columns
        for column in self.non_nullable_columns:
            if column in df.columns:
                null_mask = df[column].isnull()
                null_count = null_mask.sum()
                
                if null_count > 0:
                    missing_data_result['has_missing_data'] = True
                    missing_data_result['missing_by_column'][column] = {
                        'count': int(null_count),
                        'rows': df[null_mask].index.tolist()
                    }
        
        # Check for rows with significant missing data (>50% missing)
        missing_threshold = len(df.columns) * 0.5
        rows_with_many_missing = df[df.isnull().sum(axis=1) > missing_threshold]
        if not rows_with_many_missing.empty:
            missing_data_result['has_missing_data'] = True
            missing_data_result['rows_with_many_missing'] = rows_with_many_missing.index.tolist()
        
        missing_data_result['total_missing_values'] = int(df.isnull().sum().sum())
        
        return missing_data_result
    
    def _check_data_quality(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Check for data quality issues.
        
        Args:
            df: DataFrame to check
            
        Returns:
            List of quality issues
        """
        quality_issues = []
        
        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            quality_issues.append({
                'type': 'duplicate_rows',
                'message': f"Found {duplicate_count} duplicate rows",
                'count': int(duplicate_count)
            })
        
        # Check for columns with all same values
        for column in df.columns:
            if df[column].nunique() == 1:
                quality_issues.append({
                    'type': 'constant_column',
                    'message': f"Column '{column}' has the same value for all rows",
                    'column': column
                })
        
        # Check for unusual data patterns (e.g., very long strings)
        for column in df.select_dtypes(include=['object']).columns:
            if df[column].astype(str).str.len().max() > 1000:
                quality_issues.append({
                    'type': 'long_text',
                    'message': f"Column '{column}' contains unusually long text values",
                    'column': column
                })
        
        return quality_issues
    
    def _check_product_frequency(self, product: str) -> Dict[str, any]:
        """
        Check if product validation should run based on frequency schedule.
        
        Args:
            product: Product name to check
            
        Returns:
            Dict with frequency validation info
        """
        try:
            current_date = datetime.now()
            current_month = current_date.month
            
            # Get product configuration
            product_config = self.product_schedule.get(product, {})
            frequency = product_config.get('frequency', 'monthly')
            
            frequency_info = {
                'product': product,
                'frequency': frequency,
                'should_validate': True,
                'status': 'valid',
                'message': ''
            }
            
            if frequency == 'monthly':
                # Always validate monthly products
                frequency_info['message'] = 'Monthly validation - always active'
                
            elif frequency == 'bi-annual':
                # Validate in June and December
                if current_month not in [6, 12]:
                    frequency_info['should_validate'] = False
                    frequency_info['status'] = 'skipped'
                    frequency_info['message'] = f'Bi-annual product - validation only in June/December (current: {current_date.strftime("%B")})'
                else:
                    frequency_info['message'] = f'Bi-annual validation active - {current_date.strftime("%B")}'
                    
            elif frequency == 'annual':
                # Validate only in December
                if current_month != 12:
                    frequency_info['should_validate'] = False
                    frequency_info['status'] = 'skipped'
                    frequency_info['message'] = f'Annual product - validation only in December (current: {current_date.strftime("%B")})'
                else:
                    frequency_info['message'] = 'Annual validation active - December'
            
            return frequency_info
            
        except Exception as e:
            logger.warning(f"Error checking product frequency for {product}: {str(e)}")
            return {
                'product': product,
                'frequency': 'unknown',
                'should_validate': True,
                'status': 'valid',
                'message': 'Frequency check failed - defaulting to validate'
            }

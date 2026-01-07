"""
Main entry point for the Data Validation and Notification Workflow Agent.
"""
import logging
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_validation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the data validation workflow."""
    parser = argparse.ArgumentParser(
        description='Data Validation and Notification Workflow Agent'
    )
    parser.add_argument(
        'file_path', 
        help='Path to the Excel file to validate'
    )
    parser.add_argument(
        '--sheet', 
        help='Name of the sheet to validate (optional)',
        default=None
    )
    parser.add_argument(
        '--config', 
        help='Path to configuration file',
        default='config.yaml'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate file exists
        file_path = Path(args.file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)

        # Initialize workflow
        logger.info("Initializing data validation workflow...")
        workflow = ValidationWorkflow()

        # Run workflow
        logger.info(f"Starting validation for file: {file_path}")
        result = workflow.run(str(file_path), args.sheet)

        # Print results
        print("\n" + "="*50)
        print("VALIDATION RESULTS")
        print("="*50)
        print(f"File: {result.get('file_path', 'N/A')}")
        print(f"Valid: {result.get('validation_result', {}).get('is_valid', False)}")
        summary = result.get('validation_result', {}).get('summary', {})
        print(f"Total Rows: {summary.get('total_rows', 0)}")
        print(f"Total Columns: {summary.get('total_columns', 0)}")
        print(f"Notification: {result.get('notification_type', 'N/A')}")

        errors = result.get('validation_result', {}).get('errors', [])
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error.get('message', 'Unknown error')}")

        warnings = result.get('validation_result', {}).get('warnings', [])
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning.get('message', 'Unknown warning')}")

        missing_data = result.get('validation_result', {}).get('missing_data_details', {})
        if missing_data.get('has_missing_data'):
            print("\nMissing Data Details:")
            if missing_data.get('missing_by_column'):
                for column, details in missing_data['missing_by_column'].items():
                    print(f"  - {column}: {details['count']} missing values")

        print("="*50)

        # Exit with appropriate code
        if result.get('validation_result', {}).get('is_valid', False):
            logger.info("Validation completed successfully")
            sys.exit(0)
        else:
            logger.warning("Validation completed with issues")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

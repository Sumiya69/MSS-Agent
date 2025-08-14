"""
Workflow orchestration for data validation and notification using LangChain.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from agents.data_validator import DataValidator
from agents.email_notifier import EmailNotifier

logger = logging.getLogger(__name__)

class ValidationWorkflow:
    """Orchestrates the data validation and notification workflow."""
    
    def __init__(self):
        """Initialize the validation workflow."""
        self.validator = DataValidator()
        self.notifier = EmailNotifier()

    def run_all_sheets(self, file_path: str) -> Dict[str, Any]:
        """
        Run validation for all sheets and send a single aggregated notification.
        
        Args:
            file_path: Path to Excel file to validate
            
        Returns:
            Dict containing aggregated validation and notification results
        """
        import pandas as pd
        
        workflow_result = {
            'workflow_id': f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now().isoformat(),
            'file_path': file_path,
            'all_sheets_results': {},
            'aggregated_result': None,
            'notification_sent': False,
            'workflow_status': 'started'
        }
        
        try:
            logger.info(f"Multi-sheet workflow started for file: {file_path}")
            
            # Get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Validate each sheet
            all_errors = []
            all_valid = True
            
            for sheet in sheet_names:
                sheet_result = self.run(file_path, sheet)
                workflow_result['all_sheets_results'][sheet] = sheet_result
                
                validation_result = sheet_result.get('validation_result', {})
                if not validation_result.get('is_valid', False):
                    all_valid = False
                    errors = validation_result.get('errors', [])
                    for error in errors:
                        error['sheet'] = sheet
                        all_errors.append(error)
            
            # Check periodic logic based on frequency and deadlines
            now = datetime.now()
            product_schedule = getattr(self.validator, 'product_schedule', {})
            should_send_periodic = False
            
            for product, schedule in product_schedule.items():
                freq = schedule.get('frequency')
                deadline_day = schedule.get('deadline_day')
                
                # Monthly: 3rd/4th week (7 days before deadline)
                if freq == 'monthly' and now.day >= int(deadline_day) - 7:
                    should_send_periodic = True
                # Bi-annual: 7 days before deadline
                elif freq == 'bi-annual':
                    months = schedule.get('deadline_months', [])
                    if now.month in months and now.day >= int(deadline_day) - 7:
                        should_send_periodic = True
                # Annual: 28 days before deadline (February for March deadline)
                elif freq == 'annual':
                    month = schedule.get('deadline_month')
                    if now.month == month and now.day >= int(deadline_day) - 28:
                        should_send_periodic = True
            
            # Aggregate results
            aggregated_result = {
                'file_path': file_path,
                'validation_timestamp': datetime.now().isoformat(),
                'total_sheets': len(sheet_names),
                'is_valid': all_valid,
                'errors': all_errors,
                'summary': {
                    'sheets_processed': sheet_names,
                    'total_errors': len(all_errors),
                    'errors_by_sheet': {sheet: len([e for e in all_errors if e.get('sheet') == sheet]) for sheet in sheet_names}
                },
                'periodic_trigger': should_send_periodic
            }
            
            workflow_result['aggregated_result'] = aggregated_result
            
            # Send only one summary email per run
            if not all_valid or should_send_periodic:
                logger.info("Sending aggregated missing data notification")
                # Add file name to notification message
                aggregated_result['message'] = f"File '{file_path}' has missing/invalid data. Please check the attached summary."
                notification_sent = self.notifier.send_missing_data_notification(aggregated_result)
                workflow_result['notification_type'] = 'missing_data_aggregated'
                workflow_result['workflow_status'] = 'completed_with_issues'
            else:
                logger.info("All sheets valid - sending completion notification")
                aggregated_result['message'] = f"File '{file_path}' has no issues. All sheets validated successfully."
                notification_sent = self.notifier.send_completion_notification(aggregated_result)
                workflow_result['notification_type'] = 'completion_aggregated'
                workflow_result['workflow_status'] = 'completed_success'

            workflow_result['notification_sent'] = notification_sent
            logger.info(f"Multi-sheet workflow finished for file: {file_path}")
            
        except Exception as e:
            logger.error(f"Multi-sheet workflow execution error: {str(e)}")
            workflow_result['error'] = str(e)
            workflow_result['workflow_status'] = 'failed'
        
        workflow_result['end_time'] = datetime.now().isoformat()
        return workflow_result

    def run(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the workflow: validate data, send notification if needed.
        
        Args:
            file_path: Path to Excel file to validate
            sheet_name: Optional sheet name to validate
            
        Returns:
            Dict containing validation and notification results
        """
        workflow_result = {
            'workflow_id': f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now().isoformat(),
            'file_path': file_path,
            'sheet_name': sheet_name,
            'validation_result': None,
            'notification_sent': False,
            'workflow_status': 'started'
        }
        
        try:
            logger.info(f"Workflow started for file: {file_path}")

            # Step 1: Validate the data
            validation_result = self.validator.validate_spreadsheet(file_path, sheet_name)
            workflow_result['validation_result'] = validation_result

            # Step 2: Frequency/deadline-based notification logic
            now = datetime.now()
            product_schedule = getattr(self.validator, 'product_schedule', {})
            df = validation_result['summary'].get('dataframe') if 'dataframe' in validation_result['summary'] else None
            notification_sent = False
            notification_type = None

            if df is not None:
                for product, schedule in product_schedule.items():
                    freq = schedule.get('frequency')
                    deadline_day = schedule.get('deadline_day')
                    # Monthly
                    if freq == 'monthly' and now.day >= int(deadline_day) - 7:
                        if product in df.get('Product', []):
                            notification_sent = self.notifier.send_missing_data_notification(validation_result)
                            notification_type = f'missing_data_{product}_monthly'
                    # Bi-annual
                    elif freq == 'bi-annual':
                        months = schedule.get('deadline_months', [])
                        if now.month in months and now.day >= int(deadline_day) - 7:
                            if product in df.get('Product', []):
                                notification_sent = self.notifier.send_missing_data_notification(validation_result)
                                notification_type = f'missing_data_{product}_biannual'
                    # Annual
                    elif freq == 'annual':
                        month = schedule.get('deadline_month')
                        if now.month == month and now.day >= int(deadline_day) - 28:
                            if product in df.get('Product', []):
                                notification_sent = self.notifier.send_missing_data_notification(validation_result)
                                notification_type = f'missing_data_{product}_annual'

            # Fallback: regular notification if not frequency-based
            if not notification_sent:
                if not validation_result.get('is_valid', False):
                    logger.info("Data validation failed - sending missing data notification")
                    notification_sent = self.notifier.send_missing_data_notification(validation_result)
                    notification_type = 'missing_data'
                    workflow_result['workflow_status'] = 'completed_with_issues'
                else:
                    logger.info("Data validation passed - sending completion notification")
                    notification_sent = self.notifier.send_completion_notification(validation_result)
                    notification_type = 'completion'
                    workflow_result['workflow_status'] = 'completed_success'
            else:
                workflow_result['workflow_status'] = 'completed_with_issues'

            workflow_result['notification_sent'] = notification_sent
            workflow_result['notification_type'] = notification_type

            logger.info(f"Workflow finished for file: {file_path}")

        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            workflow_result['error'] = str(e)
            workflow_result['workflow_status'] = 'failed'

        workflow_result['end_time'] = datetime.now().isoformat()
        return workflow_result

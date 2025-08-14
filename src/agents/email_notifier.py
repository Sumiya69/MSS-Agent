"""
Email notification agent for sending alerts about data validation issues.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
import logging
from datetime import datetime
from pathlib import Path
import jinja2

from utils.config import config

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Agent responsible for sending email notifications."""
    
    def __init__(self):
        self.email_config = config.email_config
        self.business_unit_config = config.business_unit_config
        self.notification_config = config.notification_config
        
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent.parent.parent / "templates"
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )
    
    def send_missing_data_notification(self, validation_result: Dict[str, any]) -> bool:
        """
        Send email notification about missing data.
        
        Args:
            validation_result: Results from data validation
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Prepare email content
            subject = self._generate_subject()
            body = self._generate_email_body(validation_result)
            
            # Get recipients
            recipients = self._get_recipients()
            
            # Send email
            success = self._send_email(
                subject=subject,
                body=body,
                recipients=recipients,
                is_html=True
            )
            
            if success:
                logger.info(f"Missing data notification sent successfully to {recipients}")
            else:
                logger.error("Failed to send missing data notification")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending missing data notification: {str(e)}")
            return False
    
    def send_completion_notification(self, validation_result: Dict[str, any]) -> bool:
        """
        Send notification when validation is complete with no issues.
        
        Args:
            validation_result: Results from data validation
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "Data Validation Complete - No Issues Found"
            body = self._generate_completion_email_body(validation_result)
            recipients = self._get_recipients()
            
            success = self._send_email(
                subject=subject,
                body=body,
                recipients=recipients,
                is_html=True
            )
            
            if success:
                logger.info(f"Completion notification sent successfully to {recipients}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending completion notification: {str(e)}")
            return False
    
    def _generate_subject(self) -> str:
        """Generate email subject."""
        template = self.notification_config.get(
            'subject_template', 
            'Data Validation Alert - Missing Data Found'
        )
        return f"{template} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    def _generate_email_body(self, validation_result: Dict[str, any]) -> str:
        """
        Generate HTML email body for missing data notification.
        
        Args:
            validation_result: Validation results
            
        Returns:
            str: HTML email body
        """
        try:
            template = self.template_env.get_template('email_template.html')
            return template.render(
                validation_result=validation_result,
                business_unit=self.business_unit_config.get('name', 'Business Unit'),
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        except jinja2.TemplateNotFound:
            # Fallback to simple text template
            return self._generate_simple_email_body(validation_result)
    
    def _generate_simple_email_body(self, validation_result: Dict[str, any]) -> str:
        """Generate simple text email body as fallback."""
        # Use .get() method to safely access all keys
        missing_data = validation_result.get('missing_data_details', {})
        summary = validation_result.get('summary', {})
        
        body = f"""
        <html>
        <body>
        <h2>Data Validation Alert</h2>
        <p>Dear {self.business_unit_config.get('name', 'Team')},</p>

        <p>Our automated data validation process has detected issues in the master spreadsheet.</p>

        <h3>Validation Summary:</h3>
        <ul>
        <li><strong>File:</strong> {validation_result.get('file_path', 'N/A')}</li>
        <li><strong>Sheet:</strong> {validation_result.get('sheet_name', 'N/A')}</li>
        <li><strong>Total Rows:</strong> {summary.get('total_rows', 0)}</li>
        <li><strong>Valid Rows:</strong> {summary.get('valid_rows', 0)}</li>
        <li><strong>Error Rows:</strong> {summary.get('error_rows', 0)}</li>
        <li><strong>Validation Rate:</strong> {summary.get('validation_rate', 0):.1f}%</li>
        <li><strong>Validation Time:</strong> {validation_result.get('validation_timestamp', 'N/A')}</li>
        </ul>

        <h3>Missing Data Details:</h3>
        """

        if missing_data.get('missing_by_column'):
            body += "<ul>"
            for column, details in missing_data.get('missing_by_column', {}).items():
                body += f"<li><strong>{column}:</strong> {details.get('count', 0)} missing values</li>"
            body += "</ul>"

        if missing_data.get('missing_rows'):
            body += f"<p><strong>Empty rows found:</strong> {len(missing_data.get('missing_rows', []))} rows</p>"
        
        # Add product issue summary if available
        product_issues = validation_result.get('product_issue_results', [])
        if product_issues:
            error_issues = [p for p in product_issues if p.get('status') != 'valid']
            if error_issues:
                body += f"<h3>Product/Issue Validation Errors:</h3><ul>"
                for issue in error_issues[:10]:  # Limit to first 10 for email brevity
                    body += f"<li><strong>Row {issue.get('row_index', 'N/A')}:</strong> {issue.get('product', 'N/A')} - {issue.get('details', 'No details')}</li>"
                if len(error_issues) > 10:
                    body += f"<li><em>... and {len(error_issues) - 10} more issues</em></li>"
                body += "</ul>"
        
        body += """
        <p>Please review and update the data as soon as possible.</p>
        
        <p>Best regards,<br>
        Data Validation System</p>
        </body>
        </html>
        """
        
        return body
    
    def _generate_completion_email_body(self, validation_result: Dict[str, any]) -> str:
        """Generate email body for completion notification."""
        # Use .get() method to safely access all keys
        summary = validation_result.get('summary', {})
        
        return f"""
        <html>
        <body>
        <h2>Data Validation Complete</h2>
        <p>Dear {self.business_unit_config.get('name', 'Team')},</p>
        
        <p>Good news! The data validation process has completed successfully with no issues found.</p>
        
        <h3>Validation Summary:</h3>
        <ul>
        <li><strong>File:</strong> {validation_result.get('file_path', 'N/A')}</li>
        <li><strong>Sheet:</strong> {validation_result.get('sheet_name', 'N/A')}</li>
        <li><strong>Total Rows:</strong> {summary.get('total_rows', 0)}</li>
        <li><strong>Valid Rows:</strong> {summary.get('valid_rows', 0)}</li>
        <li><strong>Total Columns:</strong> {summary.get('total_columns', 0)}</li>
        <li><strong>Validation Rate:</strong> {summary.get('validation_rate', 0):.1f}%</li>
        <li><strong>Validation Time:</strong> {validation_result.get('validation_timestamp', 'N/A')}</li>
        </ul>
        
        <p>All required data is present and the spreadsheet is ready for processing.</p>
        
        <p>Best regards,<br>
        Data Validation System</p>
        </body>
        </html>
        """
    
    def _get_recipients(self) -> List[str]:
        """Get email recipients list."""
        recipients = [self.business_unit_config.get('email')]
        cc_emails = self.business_unit_config.get('cc_emails', [])
        recipients.extend(cc_emails)
        return [email for email in recipients if email]  # Filter out None values
    
    def _send_email(self, subject: str, body: str, recipients: List[str], 
                   is_html: bool = True, attachments: Optional[List[str]] = None) -> bool:
        """
        Send email using SMTP.
        
        Args:
            subject: Email subject
            body: Email body
            recipients: List of recipient emails
            is_html: Whether body is HTML
            attachments: Optional list of file paths to attach
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('sender_email')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    self._add_attachment(msg, file_path)
            
            # Setup SMTP connection
            context = ssl.create_default_context()
            
            # Add detailed logging for demo purposes
            logger.info(f"Initiating SMTP connection to {self.email_config.get('smtp_server')}:{self.email_config.get('smtp_port')}")
            logger.info(f"Email sender: {self.email_config.get('sender_email')}")
            logger.info(f"Email recipients: {recipients}")
            logger.info(f"Email subject: {subject}")
            
            with smtplib.SMTP(
                self.email_config.get('smtp_server'), 
                self.email_config.get('smtp_port')
            ) as server:
                logger.info("SMTP connection established, starting TLS...")
                server.starttls(context=context)
                
                logger.info("Authenticating with SMTP server...")
                server.login(
                    self.email_config.get('sender_email'),
                    self.email_config.get('sender_password')
                )
                logger.info("SMTP authentication successful")
                
                # Send email
                text = msg.as_string()
                logger.info("Sending email message...")
                server.sendmail(
                    self.email_config.get('sender_email'),
                    recipients,
                    text
                )
                logger.info("Email sent successfully via SMTP")
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add file attachment to email message."""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {Path(file_path).name}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {str(e)}")

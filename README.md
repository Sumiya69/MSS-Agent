# Data Validation and Notification Workflow Agent

A Python-based agent that validates data in Excel spreadsheets and sends email notifications for missing or incorrect data.

## Features

- Upload and parse Excel files with automatic sheet detection
- Validate data for missing values, incorrect data types, and required columns
- Send email notifications to business units with detailed validation reports
- Automated workflow orchestration with LangChain
- Interactive Streamlit web interface for file uploads and validation
- Real-time display of validation results and data preview
- Support for multiple Excel sheets with user selection

## Project Structure

```
mss/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── data_validator.py      # Data validation logic and rules
│   │   └── email_notifier.py      # Email notification system
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── excel_parser.py        # Excel file parsing and sheet detection
│   │   └── config.py              # Configuration loader
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── validation_workflow.py # Workflow orchestration
│   ├── main.py                    # CLI entry point
│   └── ui_app.py                  # Streamlit web interface
├── tests/
│   ├── __init__.py
│   ├── test_data_validator.py
│   └── test_excel_parser.py
├── data/
│   └── uploaded.xlsx              # Uploaded files stored here
├── templates/
│   └── email_template.html        # Email notification template
├── requirements.txt               # Python dependencies
├── config.yaml                    # Application configuration
└── README.md
```

## Installation

1. **Install Python 3.12** (Required due to dependency compatibility):
   - Download from [python.org](https://python.org)
   - Ensure Python 3.12 is used (not 3.13+ due to pydantic-core issues)

2. **Install Rust/Cargo** (Required for building pydantic-core):
   ```bash
   # Install from https://rustup.rs/ or use:
   winget install Rustlang.Rustup
   ```

3. **Configure Python Environment**:
   ```bash
   # Use the configure_python_environment tool in VS Code
   # Or manually create a virtual environment
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure email settings** in `config.yaml`:
   - Set up SMTP server details
   - Use Gmail app password for authentication

## Usage


### Activate Python 3.12 Environment and Run UI (Windows PowerShell)
```powershell
.\venv\,Scripts\Activate
streamlit run src/ui_app.py
```

### CLI Interface
```bash
python src/main.py --file-path "path/to/your/file.xlsx" --sheet-name "SheetName"
```

### Web Interface
```bash
streamlit run src/ui_app.py
```
Then:
1. Upload your Excel file via the web interface
2. Select the sheet you want to validate from the dropdown
3. Click "Run Validation" to process the data
4. View validation results, errors, warnings, and data preview
5. Email notifications are sent automatically if issues are found

## Configuration

Edit `config.yaml` to set up:
- Email SMTP settings (Gmail app password recommended)
- Business unit contact information
- Validation rules and required columns
- File upload settings and limits

## Recent Updates

### Version 2.0 - Enhanced UI and Validation
- **Streamlit Web Interface**: Added interactive web UI for file uploads
- **Sheet Detection**: Automatic detection and selection of Excel sheets
- **Enhanced Validation**: Detailed validation reports with errors, warnings, and summaries
- **Data Preview**: Real-time preview of uploaded Excel data
- **Session Management**: Proper state management for file uploads and sheet selection
- **File Name Display**: Shows actual uploaded file name for confirmation
- **Error Handling**: Improved error messages and user feedback

### Key Improvements Made:
1. **Multi-sheet Support**: Users can select which sheet to validate from dropdown
2. **Visual Feedback**: Clear display of validation results, data types, and null counts
3. **State Management**: Prevents UI issues with multiple file uploads
4. **Data Preview**: Shows first 10 rows of selected sheet after validation
5. **Environment Setup**: Resolved Python 3.13 compatibility issues with proper dependencies

### Dependencies Resolved:
- **Python Version**: Switched to Python 3.12 for compatibility
- **Rust/Cargo**: Added for building pydantic-core dependency
- **Email Authentication**: Configured Gmail app passwords for SMTP

## Troubleshooting

### Common Issues:
1. **Python 3.13 Compatibility**: Use Python 3.12 instead
2. **Rust Missing**: Install Rust/Cargo from rustup.rs
3. **Email Errors**: Use Gmail app password, not regular password
4. **Sheet Selection**: Refresh Streamlit page if old sheet names persist

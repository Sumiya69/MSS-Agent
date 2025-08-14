"""
Database connection and data retrieval utilities.
"""
import sqlite3
import pandas as pd
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import io
import os

from utils.config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and data retrieval."""
    
    def __init__(self):
        self.db_config = getattr(config, 'database', {})
        self.data_source_config = getattr(config, 'data_source', {})
        self.connection = None
        
    def connect(self):
        """Establish database connection."""
        try:
            db_type = self.db_config.get('type', 'sqlite')
            if db_type == 'sqlite':
                db_path = self.db_config.get('connection_string', 'sqlite:///data/validation_data.db')
                db_file = db_path.replace('sqlite:///', '')
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(db_file), exist_ok=True)
                
                self.connection = sqlite3.connect(db_file)
                logger.info(f"Connected to SQLite database: {db_file}")
                
                # Initialize tables if they don't exist
                self._initialize_tables()
                
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False
    
    def _initialize_tables(self):
        """Initialize database tables if they don't exist."""
        try:
            cursor = self.connection.cursor()
            
            # Create validation_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_data BLOB NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_type TEXT,
                    sheet_names TEXT,
                    metadata TEXT
                )
            ''')
            
            self.connection.commit()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database tables: {str(e)}")
    
    def store_file_data(self, filename: str, file_data: bytes, file_type: str = 'xlsx', 
                       sheet_names: List[str] = None, metadata: Dict = None) -> bool:
        """Store file data in database."""
        try:
            cursor = self.connection.cursor()
            
            sheet_names_str = ','.join(sheet_names) if sheet_names else ''
            metadata_str = str(metadata) if metadata else ''
            
            cursor.execute('''
                INSERT INTO validation_data (filename, file_data, file_type, sheet_names, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, file_data, file_type, sheet_names_str, metadata_str))
            
            self.connection.commit()
            logger.info(f"File data stored successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing file data: {str(e)}")
            return False
    
    def get_available_files(self) -> List[Dict]:
        """Get list of available files in database."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT id, filename, upload_date, file_type, sheet_names
                FROM validation_data
                ORDER BY upload_date DESC
            ''')
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'id': row[0],
                    'filename': row[1],
                    'upload_date': row[2],
                    'file_type': row[3],
                    'sheet_names': row[4].split(',') if row[4] else []
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error retrieving available files: {str(e)}")
            return []
    
    def get_file_data(self, file_id: int) -> Optional[bytes]:
        """Retrieve file data from database."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('SELECT file_data FROM validation_data WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            
            if row:
                return row[0]
            else:
                logger.warning(f"File with ID {file_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving file data: {str(e)}")
            return None
    
    def get_file_info(self, file_id: int) -> Optional[Dict]:
        """Get file information by ID."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT filename, upload_date, file_type, sheet_names, metadata
                FROM validation_data WHERE id = ?
            ''', (file_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'filename': row[0],
                    'upload_date': row[1],
                    'file_type': row[2],
                    'sheet_names': row[3].split(',') if row[3] else [],
                    'metadata': row[4]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving file info: {str(e)}")
            return None
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

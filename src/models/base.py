"""
Base model classes and database setup for the Financial Tracker application.

This module provides the base SQLAlchemy model class and database initialization.
"""

from datetime import datetime
from typing import Any, Dict

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class BaseModel(db.Model):
    """
    Base model class that provides common fields and methods for all models.
    
    Attributes:
        id: Primary key for the model
        created_at: Timestamp when the record was created
        updated_at: Timestamp when the record was last updated
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs) -> None:
        """
        Update model instance with provided keyword arguments.
        
        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def save(self) -> 'BaseModel':
        """
        Save the model instance to the database.
        
        Returns:
            The saved model instance
        """
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

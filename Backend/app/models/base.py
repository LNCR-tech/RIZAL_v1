"""Use: Defines database models for the shared SQLAlchemy base class.
Where to use: Use this when the backend needs to store or load the shared SQLAlchemy base class data.
Role: Model layer. It maps Python objects to database tables and relationships.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

"""User model for Flask-Login compatibility."""

from flask_login import UserMixin


class User(UserMixin):
    """Flask-Login compatible User class."""
    
    def __init__(self, user_id, username=None):
        """Initialize User with ID and optional username."""
        self.id = str(user_id)
        self.username = username
    
    def get_id(self):
        """Return user ID as string for Flask-Login."""
        return self.id
    
    @property
    def is_authenticated(self):
        """User is always authenticated if User object exists."""
        return True
    
    @property
    def is_active(self):
        """User is always active."""
        return True
    
    @property
    def is_anonymous(self):
        """User is never anonymous."""
        return False
    
    def to_dict(self):
        """Convert user to dictionary for serialization."""
        return {
            'id': self.id,
            'username': self.username
        }
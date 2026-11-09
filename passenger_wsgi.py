import sys
import os

# Add application root path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app instance as application
from app import app as application
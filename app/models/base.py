from sqlalchemy.orm import declarative_base

# Creating a declarative base for the auth models.
# In a real integration, this might be imported from the main app's database module.
Base = declarative_base()

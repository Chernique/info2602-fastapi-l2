import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select, func
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """Reset the database and add sample data"""
    with get_session() as db:
        drop_all() # delete all tables
        create_db_and_tables() # recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass')
        db.add(bob)
        db.commit()
        db.refresh(bob)
        print("Database Initialized")

@cli.command()
def get_user(username: str):
    """
    Find a specific user by their exact username
    
    Args:
        username: The exact username to search for
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"Sorry, '{username}' not found!")
            return
        print(user)

@cli.command()
def get_all_users():
    """Display every user in the database"""
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found in database")
        else:
            print(f"All users ({len(all_users)} total):")
            for user in all_users:
                print(user)

@cli.command()
def change_email(username: str, new_email: str):
    """
    Update a user's email address
    
    Args:
        username: Username of the account to modify
        new_email: The new email address to set
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"Can't find '{username}' - email not updated")
            return
        old_email = user.email
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Changed {user.username}'s email from {old_email} to {user.email}")

@cli.command()
def create_user(username: str, email: str, password: str):
    """
    Add a new user to the database
    
    Args:
        username: Desired username (must be unique)
        email: Email address (must be unique)
        password: Plain text password (will be hashed)
    """
    with get_session() as db:
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
            print(f"Successfully created: {newuser}")
        except IntegrityError:
            db.rollback()
            print("Error: That username or email is already taken. Try something else.")

@cli.command()
def delete_user(username: str):
    """
    Remove a user from the database permanently
    
    Args:
        username: Username of the account to delete
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"Can't find '{username}' - nothing was deleted")
            return
        db.delete(user)
        db.commit()
        print(f"Deleted user: {username}")

@cli.command()
def search_user(search_term: str):
    """
    Find users by partial matching (username OR email)
    
    Args:
        search_term: Text to search for (case sensitive, partial matches work)
    
    Examples:
        python app/cli.py search-user bob    # finds bob, bobby, bob123
        python app/cli.py search-user mail   # finds any email with 'mail'
    """
    with get_session() as db:
        users = db.exec(
            select(User).where(
                (User.username.contains(search_term)) | 
                (User.email.contains(search_term))
            )
        ).all()
        
        if not users:
            print(f"No users found matching '{search_term}'")
        else:
            print(f"Found {len(users)} user(s) matching '{search_term}':")
            for user in users:
                print(user)

@cli.command()
def list_users(limit: int = 10, offset: int = 0):
    """
    Show users in chunks for pagination
    
    Args:
        limit: Maximum number of users to show (default: 10)
        offset: How many users to skip from the start (default: 0)
    
    Examples:
        python app/cli.py list-users              # First 10 users
        python app/cli.py list-users --limit 5    # First 5 users
        python app/cli.py list-users --offset 10  # Skip first 10, show next 10
    """
    with get_session() as db:
        # Get total count for context
        total = db.exec(select(func.count(User.id))).one()
        
        users = db.exec(
            select(User).offset(offset).limit(limit)
        ).all()
        
        if not users:
            print(f"No users found (offset={offset}, limit={limit})")
        else:
            print(f"Showing {len(users)} users (offset {offset}, limit {limit})")
            print(f"Total users in database: {total}")
            print("-" * 40)
            for user in users:
                print(user)

if __name__ == "__main__":
    cli()
import logging
from datetime import timedelta
from typing import List

from sqlalchemy.orm import Session

from core_system.models.char_temp import CharTemp
from core_system.models.user import User, UserChar, UserData, UserTeamMember
from util.auth import create_access_token, get_password_hash, verify_password
from core_system.config import ACCESS_TOKEN_EXPIRE_MINUTES

# Default values for new user creation
DEFAULT_STARTING_CHAR_IDS = [1,2]
DEFAULT_STARTING_MAP_ID = 1
DEFAULT_STARTING_AREA_ID = 1


class AuthenticationError(Exception):
    pass


def authenticate_user(db: Session, username: str, password: str) -> str:
    logging.debug(f"Attempting to authenticate user: {username}")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logging.warning(f"Authentication failed: User '{username}' not found.")
        raise AuthenticationError("Invalid username or password")

    if not verify_password(password, user.hashed_password):
        logging.warning(f"Authentication failed: Invalid password for user '{username}'.")
        raise AuthenticationError("Invalid username or password")

    logging.debug(f"User '{username}' authenticated successfully. Creating access token.")
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    logging.debug(f"Access token created for user ID: {user.id}")
    return token


def get_all_users(db: Session) -> List[str]:
    """Retrieves a list of all usernames."""
    logging.debug("Fetching all users.")
    users = db.query(User).all()
    if not users:
        logging.debug("No users found in the database.")
        return []
    usernames = [user.username for user in users]
    logging.debug(f"Found {len(usernames)} users.")
    return usernames


def add_user(db: Session, username: str, password: str) -> User:
    """
    Creates a user object, hashes the password, and adds it to the session.
    This function does NOT commit the transaction.
    """
    logging.debug(f"Hashing password for user '{username}'.")
    hashed_password = get_password_hash(password)
    new_user = User(username=username,
                    hashed_password=hashed_password)
    db.add(new_user)
    logging.debug(f"User object for '{username}' added to session.")
    # We flush the session to get the new_user.id for subsequent operations
    # within the same transaction.
    db.flush()
    logging.debug(f"Session flushed. New user ID is {new_user.id}.")
    return new_user


def create_user_data(db: Session, user_id: int) -> UserData:
    """
    Creates default user data and adds it to the session.
    This function does NOT commit the transaction.
    """
    logging.debug(f"Creating default UserData for user_id: {user_id}.")
    new_user_data = UserData(user_id=user_id,
                             money=0,
                             current_map_id=DEFAULT_STARTING_MAP_ID,
                             current_area_id=DEFAULT_STARTING_AREA_ID)
    db.add(new_user_data)
    logging.debug(f"UserData for user_id {user_id} added to session.")
    db.flush()
    logging.debug(f"Session flushed. New UserData ID is {new_user_data.id}.")
    return new_user_data


def create_user_char(db: Session, char_id: int, target_user_data_id: int) -> UserChar:
    """
    Creates a default starting character for the user and adds it to the session.
    This function does NOT commit the transaction.
    :param target_user_data_id: The ID of the UserData record this character belongs to.
    """
    logging.debug(f"Creating UserChar from template char_id: {char_id} for user_data_id: {target_user_data_id}.")
    char_temp = db.query(CharTemp).filter(CharTemp.id == char_id).first()
    if not char_temp:
        # It's good practice to handle cases where the template character doesn't exist.
        logging.error(f"Character template with id {char_id} not found during UserChar creation.")
        raise ValueError(f"Character template with id {char_id} not found.")

    new_user_char = UserChar(
        user_data_id=target_user_data_id,   # Assigns this character to a specific user_data record
        char_temp_id=char_temp.id,          # Specifies the template source
        level=1,
        exp=0,
        hp=char_temp.base_hp,               # Fill initial stats based on the template
        mp=char_temp.base_mp,
        atk=char_temp.base_atk,
        spd=char_temp.base_spd,
        def_=char_temp.base_def,
        status_effects={},                  # No status effects initially
        is_locked=False
    )
    db.add(new_user_char)
    logging.debug(f"UserChar object for template {char_id} added to session.")
    return new_user_char

def create_user_with_defaults(db: Session, username: str, password: str) -> User:
    """
    Handles the business logic for creating a new user with all their default data.
    This function orchestrates adding the user, their data, and their starting character.
    It does NOT commit the transaction; the caller (e.g., the API router) is
    responsible for handling the transaction's commit or rollback.
    """
    try:
        logging.info(f"Attempting to create user '{username}' with default data.")

        # Step 1: Create the core user account
        logging.debug("Calling add_user service...")
        new_user = add_user(db=db, username=username, password=password)
        logging.info(f"Step 1/4: User '{username}' (ID: {new_user.id}) added to session.")

        # Step 2: Create associated game data
        logging.debug(f"Calling create_user_data for user_id: {new_user.id}...")
        new_user_data = create_user_data(db=db, user_id=new_user.id)
        logging.info(f"Step 2/4: UserData for user ID {new_user.id} (UserData ID: {new_user_data.id}) created.")

        # Step 3: Create the default starting characters
        logging.debug(f"Creating default characters from IDs: {DEFAULT_STARTING_CHAR_IDS}")
        starting_chars = [
            create_user_char(db=db, char_id=char_id, target_user_data_id=new_user_data.id)
            for char_id in DEFAULT_STARTING_CHAR_IDS
        ]
        logging.info(f"Step 3/4: {len(starting_chars)} default characters created for UserData ID {new_user_data.id}.")

        # Step 4: Create the default starting team
        db.flush()  # Ensure starting_chars get their IDs
        starting_char_ids = [char.id for char in starting_chars]
        logging.debug(f"Calling create_team for user_data_id: {new_user_data.id} with char_ids: {starting_char_ids}")
        create_team(db=db, user_data=new_user_data, selected_char_ids=starting_char_ids)
        logging.info(f"Step 4/4: Default team created for UserData ID {new_user_data.id}.")

        logging.info(f"Successfully prepared user '{username}' for creation.")
        return new_user
    except Exception as e:
        # Log the specific error that occurred during the process
        logging.error(
            f"Failed to create user '{username}' with defaults. Error: {e}",
            exc_info=True  # This will include the full traceback in the log
        )
        # Re-raise the exception so the router can handle the transaction rollback
        # and return an appropriate HTTP error.
        raise


def create_team(db: Session, user_data: UserData, selected_char_ids: list[int]):
    """
    Creates or updates the user's team, with a maximum of six characters.
    This function does not commit the transaction; the caller is responsible.

    :param db: SQLAlchemy Session
    :param user_data: UserData instance
    :param selected_char_ids: A list of UserChar.id for the selected characters, in the desired order.
    """
    logging.debug(f"Updating team for user_data_id: {user_data.id} with char_ids: {selected_char_ids}")
    # The Pydantic model `UpdateTeamRequest` already validates max_length and uniqueness.
    # This check is for service-layer robustness.
    if len(selected_char_ids) > 6:
        raise ValueError("A maximum of 6 characters can be selected for a team")

    # Verify character ownership if the list is not empty
    if selected_char_ids:
        logging.debug("Verifying character ownership...")
        owned_chars_count = db.query(UserChar.id).filter(
            UserChar.user_data_id == user_data.id,
            UserChar.id.in_(selected_char_ids)
        ).count()

        if owned_chars_count != len(selected_char_ids):
            logging.error(f"Character ownership verification failed for user_data_id: {user_data.id}. "
                          f"Expected {len(selected_char_ids)} chars, found {owned_chars_count} owned chars.")
            raise ValueError("Some of the selected characters do not belong to the player or do not exist")
        logging.debug("Character ownership verified.")

    # Clear the original team. Since UserData.team_members has cascade="all, delete-orphan",
    # .clear() will mark old UserTeamMember instances for deletion.
    logging.debug(f"Clearing existing team for user_data_id: {user_data.id}. "
                  f"Current team size: {len(user_data.team_members)}")
    user_data.team_members.clear()
    logging.debug(user_data.team_members)
    db.flush()  # Ensure delete operations are flushed before adding new ones
    logging.debug("Existing team cleared and session flushed.")

    # Create new UserTeamMember instances, preserving the order from the input list
    logging.debug("Creating new team members...")
    for idx, char_id in enumerate(selected_char_ids):
        team_member = UserTeamMember(
            # user_data_id is set automatically by the relationship
            user_char_id=char_id,
            position=idx
        )
        user_data.team_members.append(team_member)
        logging.debug(f"Appended char_id: {char_id} to team at position: {idx}")
    logging.debug(user_data.team_members)
    logging.debug(f"Finished creating {len(selected_char_ids)} new team members.")

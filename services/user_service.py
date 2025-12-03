from agents.models.user import User
from datetime import date
import re

users:list[User] = [
    User(id="1", name="John Doe", phone="111-111-1111", date_of_birth="1960-01-01", ssn_last_4="1111"),
    User(id="2", name="Jim Beam", phone="222-222-2222", date_of_birth="1970-01-01", ssn_last_4="5678"),
    User(id="3", name="Jill Johnson", phone="333-333-3333", date_of_birth="1980-01-01", ssn_last_4="9012"),
    User(id="4", name="Jack Daniels", phone="444-444-4444", date_of_birth="1990-01-01", ssn_last_4="3456"),
]

class UserService:
    def __init__(self):
        self.users = users
    
    def get_user(self, name: str, date_of_birth: str | None = None, phone: str | None = None, ssn_last_4: str | None = None) -> User | None:
        """
        Gets a user from the database.
        """
        # short wiring of missing data
        if name is None or date_of_birth is None:
            return None

        # normalize the data
        name = name.lower().strip()
        date_of_birth = date_of_birth.strip()
        # remove all non numberic characters
        if phone is not None:
            phone_number = re.sub(r'\D', '', phone).strip()
        else:
            phone_number = ""
        if ssn_last_4 is not None:
            ssn_last_4 = re.sub(r'\D', '', ssn_last_4).strip()
        else:
            ssn_last_4 = ""

        # find a user based on the normalized data
        for user in self.users:
            db_user_name = user.name.lower().strip()
            db_user_date_of_birth = user.date_of_birth.strip()
            db_user_phone = user.phone.replace("-", "").strip()
            db_user_ssn_last_4 = user.ssn_last_4.replace("-", "").strip()
            if db_user_name == name and db_user_date_of_birth == date_of_birth and db_user_phone == phone_number and db_user_ssn_last_4 == ssn_last_4:
                return user
            if db_user_name == name and db_user_date_of_birth == date_of_birth and db_user_ssn_last_4 == ssn_last_4:
                return user
            if db_user_name == name and db_user_date_of_birth == date_of_birth and db_user_phone == phone_number:
                return user
        return None

user_service = UserService()
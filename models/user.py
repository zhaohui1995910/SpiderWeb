from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class AdminUser:
    _id: str
    username: str = field(default='')
    password: str = field(default='')
    name: str = field(default='')
    introduction: str = field(default='')
    avatar: str = field(default='')
    phone: str = field(default='')
    email: str = field(default='')
    sex: int = field(default='')
    locked: int = field(default='')
    ctime: datetime = field(default=datetime.now())
    login_time: datetime = field(default=datetime.now())
    roles: str = field(default='')

    def hash_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

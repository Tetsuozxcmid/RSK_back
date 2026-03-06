from enum import Enum


class UserEnum(str, Enum):
    Student = "student"
    Teacher = "teacher"
    Moder = "moder"
    Admin = "admin"

class UserEnumForUser(str, Enum):
    Student = "student"
    Teacher = "teacher"


class UserEnumForAdmin(str,Enum):
    Moder = "moder"
    Admin = "admin"


import enum


class DirectionEnum(str, enum.Enum):
    science = "Наука"
    sport = "Спорт"
    art = "Искусство"
    other = "Другое"

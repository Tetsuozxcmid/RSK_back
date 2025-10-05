from db.models.projects import CategoryEnum

'''мапа категорий для енума проекта'''

CATEGORY_MAP = {
    "Знания": CategoryEnum.KNOWLEDGE,
    "Взаимодействие": CategoryEnum.INTERACTION,
    "Среда": CategoryEnum.ENVIRONMENT,
    "Защита": CategoryEnum.PROTECTION,
    "Данные": CategoryEnum.DATA,
    "Автоматизация": CategoryEnum.AUTOMATION
}

def map_category_label(label: str) -> CategoryEnum:
    try:
        return CATEGORY_MAP[label]
    except KeyError:
        raise ValueError(f"Unknown category label: {label}")

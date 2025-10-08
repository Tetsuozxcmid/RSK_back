from enum import Enum

class SubmissionStatus(str, Enum):
    PENDING = "на рассмотрении"
    APPROVED = "одобрен"
    REJECTED = "отклонен"
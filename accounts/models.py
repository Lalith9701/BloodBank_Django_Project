from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DONOR', 'Donor'),
        ('REQUESTER', 'Requester'),
    )
    role  = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # Enforce unique email at DB level (case-insensitive via normalisation in view)
    email = models.EmailField(unique=True, blank=True, default='')

    def __str__(self):
        return self.username


# Predefined security questions users can choose from
SECURITY_QUESTIONS = [
    ('q1', "What is the name of your first pet?"),
    ('q2', "What is your mother's maiden name?"),
    ('q3', "What was the name of your first school?"),
    ('q4', "What is your favourite childhood movie?"),
    ('q5', "What city were you born in?"),
    ('q6', "What is the middle name of your oldest sibling?"),
    ('q7', "What was the make of your first car?"),
    ('q8', "What was the name of your childhood best friend?"),
]


class SecurityProfile(models.Model):
    """
    Stores a user's chosen security question and hashed answer.
    Answer is normalised (lowercased, stripped) before hashing
    so 'London' and 'london' both work.
    """
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_profile')
    question_key    = models.CharField(max_length=10, choices=SECURITY_QUESTIONS)
    answer_hash     = models.CharField(max_length=255)   # Django PBKDF2 hash
    reset_attempts  = models.PositiveSmallIntegerField(default=0)
    locked_until    = models.DateTimeField(null=True, blank=True)

    MAX_ATTEMPTS = 3

    def set_answer(self, plain_answer: str):
        """Normalise and hash the answer."""
        self.answer_hash = make_password(plain_answer.strip().lower())

    def check_answer(self, plain_answer: str) -> bool:
        """Verify a plain answer against the stored hash."""
        return check_password(plain_answer.strip().lower(), self.answer_hash)

    @property
    def question_text(self) -> str:
        return dict(SECURITY_QUESTIONS).get(self.question_key, '')

    def __str__(self):
        return f"SecurityProfile({self.user.username})"

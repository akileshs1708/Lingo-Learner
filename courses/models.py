from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length = 150,unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_picture = models.TextField(blank=True, null=True)
    user_level = models.IntegerField(default=1)
    xp_points = models.IntegerField(default=0)
class Language(models.Model):
    language_id = models.AutoField(primary_key=True)
    language_name = models.CharField(max_length=50, unique=True)
    language_code = models.CharField(max_length=10, unique=True)

class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    from_language = models.ForeignKey(Language, related_name='courses_from', on_delete=models.CASCADE)
    to_language = models.ForeignKey(Language, related_name='courses_to', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('from_language', 'to_language')

class Lesson(models.Model):
    lesson_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson_title = models.CharField(max_length=100)
    lesson_order = models.IntegerField()
    difficulty_level = models.IntegerField(default=1)

class Exercise(models.Model):
    exercise_id = models.AutoField(primary_key=True)
    EXERCISE_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('audio', 'Audio'),
        ('translation', 'Translation')
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    exercise_type = models.CharField(max_length=50, choices=EXERCISE_TYPES)
    question = models.TextField()
    correct_answer = models.TextField()
    choices = models.JSONField(blank=True, null=True)
    audio_url = models.TextField(blank=True, null=True)

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'lesson')

class UserXP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    xp_points = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)
    last_xp_update = models.DateTimeField(auto_now_add=True)

class Achievement(models.Model):
    achievement_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    xp_reward = models.IntegerField(default=0)

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

class Discussion(models.Model):
    discussion_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Leaderboard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rank = models.IntegerField()

    class Meta:
        ordering = ['rank']

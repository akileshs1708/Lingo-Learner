from django.contrib import admin

from django.contrib import admin
from .models import User, Language, Course, Lesson, Exercise, UserProgress, UserXP, Achievement, UserAchievement, Discussion, Leaderboard

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'xp_points', 'user_level', 'created_at', 'last_login')
    search_fields = ('username', 'email')
    list_filter = ('user_level', 'created_at')

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('language_id', 'language_name', 'language_code')
    search_fields = ('language_name', 'language_code')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'from_language', 'to_language')
    list_filter = ('from_language', 'to_language')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('lesson_id', 'course', 'lesson_title', 'lesson_order', 'difficulty_level')
    list_filter = ('course', 'difficulty_level')
    search_fields = ('lesson_title',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('exercise_id', 'lesson', 'exercise_type', 'question')
    list_filter = ('exercise_type', 'lesson')
    search_fields = ('question',)

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed_at', 'score')
    list_filter = ('completed_at',)

@admin.register(UserXP)
class UserXPAdmin(admin.ModelAdmin):
    list_display = ('user', 'xp_points', 'streak_days', 'last_xp_update')
    list_filter = ('last_xp_update',)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('achievement_id', 'title', 'xp_reward')
    search_fields = ('title',)

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'achieved_at')
    list_filter = ('achieved_at',)

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('discussion_id', 'user', 'lesson', 'created_at')
    search_fields = ('content',)
    list_filter = ('created_at',)

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank')
    list_filter = ('rank',)


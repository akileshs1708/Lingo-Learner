from django.contrib import admin
from django.urls import path, include
from .views import (login_view,register_view,language_selection_view,select_language_view,dashboard_view,
                    lesson_view, submit_answer, next_lesson,leaderboard_view, home_view,
                    profile_view,quests_view,shop_view,logout_view)
from rest_framework.routers import DefaultRouter
from .views import (UserViewSet, LanguageViewSet, CourseViewSet, LessonViewSet, ExerciseViewSet,
                    UserProgressViewSet, UserXPViewSet, AchievementViewSet, UserAchievementViewSet,
                    DiscussionViewSet, LeaderboardViewSet)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'languages', LanguageViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'user-progress', UserProgressViewSet)
router.register(r'user-xp', UserXPViewSet)
router.register(r'achievements', AchievementViewSet)
router.register(r'user-achievements', UserAchievementViewSet)
router.register(r'discussions', DiscussionViewSet)
router.register(r'leaderboard', LeaderboardViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("select-language/", language_selection_view, name="language_selection"),
    path("save-language/", select_language_view, name="select_language"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("lesson/<int:lesson_id>/", lesson_view, name="lesson"),
    path("submit_answer/", submit_answer, name="submit_answer"),
    path('next-lesson/<int:lesson_id>/', next_lesson, name='next_lesson'),
    path("leaderboard/", leaderboard_view, name="leaderboard"),
    path("profile/", profile_view, name="profile"),
    path("quests/", quests_view, name="quests"),
    path("shop/", shop_view, name="shop"),
    path("", home_view, name="home"),
    path("logout/", logout_view, name="logout"),
]

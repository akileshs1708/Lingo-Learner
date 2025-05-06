from rest_framework import viewsets
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .models import User, Language, Course, Lesson, Exercise, UserProgress, UserXP, Achievement, UserAchievement, Discussion, Leaderboard
from .serializers import (UserSerializer, LanguageSerializer, CourseSerializer, LessonSerializer, ExerciseSerializer,
                          UserProgressSerializer, UserXPSerializer, AchievementSerializer, UserAchievementSerializer,
                          DiscussionSerializer, LeaderboardSerializer)
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta, date
from django.http import JsonResponse
import json
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

class UserProgressViewSet(viewsets.ModelViewSet):
    queryset = UserProgress.objects.all()
    serializer_class = UserProgressSerializer

class UserXPViewSet(viewsets.ModelViewSet):
    queryset = UserXP.objects.all()
    serializer_class = UserXPSerializer

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class UserAchievementViewSet(viewsets.ModelViewSet):
    queryset = UserAchievement.objects.all()
    serializer_class = UserAchievementSerializer

class DiscussionViewSet(viewsets.ModelViewSet):
    queryset = Discussion.objects.all()
    serializer_class = DiscussionSerializer

class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Fetch user details from PostgreSQL database
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id, password_hash FROM courses_user WHERE username = %s", [username])
            user = cursor.fetchone()

        if user:
            user_id, stored_password_hash = user

            # Check if password matches the stored hashed password
            if check_password(password, stored_password_hash):
                # Update last login time in the database
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE courses_user SET last_login = %s WHERE user_id = %s", [datetime.now(), user_id])

                # Store user session (Manual login since we're using a custom user model)
                request.session["user_id"] = user_id
                request.session["username"] = username

                return redirect("dashboard")  # Redirect to the dashboard

        return render(request, "login.html", {"error": "Invalid username or password"})

    return render(request, "login.html")

def logout_view(request):

    return redirect("login")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if username or email already exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM courses_user WHERE username = %s OR email = %s", [username, email])
            existing_user = cursor.fetchone()

        if existing_user:
            return render(request, "register.html", {"error": "Username or email already exists"})

        # Hash password before storing
        hashed_password = make_password(password)

        # Insert new user with default attributes
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO courses_user (username, email, password_hash, user_level, xp_points, created_at, last_login, profile_picture,is_superuser)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
            """, [username, email, hashed_password, 1, 0, datetime.now(), datetime.now(), None,False])

            # Get the newly created user ID
            cursor.execute("SELECT user_id FROM courses_user WHERE username = %s", [username])
            user_id = cursor.fetchone()[0]
            cursor.execute("""
                            INSERT INTO COURSES_USERXP (XP_POINTS,STREAK_DAYS,USER_ID) VALUES (%s,%s,%s) 
                        """, [0, 0, user_id])

        # Store user_id in session for authentication
        request.session["user_id"] = user_id

        return redirect("language_selection")  # Redirect to login page after successful registration

    return render(request, "register.html")

def language_selection_view(request):
    """Display available languages for the user to choose from."""
    if "user_id" not in request.session:
        return redirect("login")  # Redirect to login if not authenticated

    with connection.cursor() as cursor:
        cursor.execute("SELECT language_id, language_name, language_code FROM courses_language")
        languages = [
            {"language_id": row[0], "language_name": row[1], "flag_url": f"/static/flags/{row[2]}.png"}
            for row in cursor.fetchall()
        ]

    return render(request, "language_selection.html", {"languages": languages})

def select_language_view(request):
    """Save the selected language in the users table and redirect to dashboard."""
    if "user_id" not in request.session:
        return redirect("login")  # Redirect to login if not authenticated

    if request.method == "POST":
        language_id = request.POST.get("language_id")
        user_id = request.session["user_id"]

        with connection.cursor() as cursor:
            cursor.execute("UPDATE courses_user SET selected_language_id = %s WHERE user_id = %s", [language_id, user_id])

        return redirect("dashboard")  # Redirect to user dashboard

    return redirect("language_selection")

def dashboard_view(request):
    if "user_id" not in request.session:
        return redirect("login")  # Redirect if not logged in

    user_id = request.session["user_id"]

    # Update streak before fetching data
    update_user_streak(user_id)

    with connection.cursor() as cursor:
        # Get user details including XP, level, language, and language flag
        cursor.execute("""
            SELECT u.username, u.user_level, u.selected_language_id, 
                   l.language_name, l.language_code
            FROM courses_user u
            JOIN courses_language l ON u.selected_language_id = l.language_id
            WHERE u.user_id = %s
        """, [user_id])
        user_data = cursor.fetchone()

        if not user_data:
            return redirect("login")  # If user data is missing, re-login

        username, user_level, language_id, language_name, language_code = user_data
        flag_url = f"/static/flags/{language_code}.png"

        # Fetch XP points and streak count
        cursor.execute("""
            SELECT xp_points, streak_days 
            FROM courses_userxp 
            WHERE user_id = %s
        """, [user_id])
        xp_data = cursor.fetchone()

        if xp_data:
            xp_points, streak_days = xp_data
        else:
            xp_points, streak_days = 0, 0  # Defaults

        # XP Progress Calculation
        xp_needed_for_current_level = (user_level - 1) * 100
        xp_needed_for_next_level = user_level * 100
        progress_percentage = ((xp_points - xp_needed_for_current_level) / (
                    xp_needed_for_next_level - xp_needed_for_current_level)) * 100
        if xp_points > xp_needed_for_next_level:
            # Level Up!
            user_level += 1
            cursor.execute(""" UPDATE courses_user SET user_level = %s WHERE user_id = %s """,
                           [user_level,user_id])

        # Fetch lessons
        cursor.execute("""
            SELECT lesson_id, lesson_title, difficulty_level 
            FROM courses_lesson 
            WHERE course_id IN (
                SELECT course_id FROM courses_course WHERE to_language_id = %s
            )
            ORDER BY lesson_order ASC
        """, [language_id])
        lessons = cursor.fetchall()

    context = {
        "username": username,
        "xp_points": xp_points,
        "user_level": user_level,
        "language_name": language_name,
        "flag_url": flag_url,
        "streak_count": streak_days,  # Using `streak_days` from `update_user_streak`
        "lessons": lessons,
        "xp_progress": round(progress_percentage, 2),
    }

    return render(request, "dashboard.html", context)

def lesson_view(request, lesson_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT lesson_title FROM courses_lesson WHERE lesson_id = %s", [lesson_id])
        lesson = cursor.fetchone()

        cursor.execute("""
            SELECT exercise_id, exercise_type, question, correct_answer, choices, audio_url FROM courses_exercise
            WHERE lesson_id = %s
        """, [lesson_id])
        exercises = cursor.fetchall()

    exercises_list = [{
        "id": ex[0],
        "type": ex[1],
        "question": ex[2],
        "correct_answer": ex[3],
        "choices": json.loads(ex[4]) if ex[4] else [],
        "audio_url": ex[5]

    } for ex in exercises]

    context = {
        "lesson_title": lesson[0],
        "lesson_id": lesson_id,
        "exercises": json.dumps(exercises_list)
    }
    return render(request, "lesson.html", context)

def submit_answer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = request.session.get("user_id")
            exercise_id = data.get("exercise_id")
            lesson_id = data.get("lesson_id")
            user_answer = data.get("user_answer").strip().lower()  # Normalize answer for comparison
            with (connection.cursor() as cursor):
                # Fetch correct answer
                cursor.execute("SELECT correct_answer FROM courses_exercise WHERE exercise_id = %s", [exercise_id])
                correct_answer = cursor.fetchone()

                if not correct_answer:
                    return JsonResponse({"error": "Exercise not found"}, status=404)

                is_correct = user_answer == correct_answer[0].strip().lower()

                if is_correct:
                    # Check if exercise is already completed
                    print(f"user_id: {user_id}, exercise_id: {exercise_id}, lesson_id: {lesson_id}")
                    cursor.execute("""
                        SELECT 1 FROM courses_userprogress 
                        WHERE user_id = %s AND lesson_id = %s AND exercise_id = %s
                    """, [user_id, lesson_id, exercise_id])

                    if not cursor.fetchone():
                        # Mark exercise as completed
                        cursor.execute("""
                            INSERT INTO courses_userprogress (completed_at, exercise_id, lesson_id, user_id)
                            VALUES (NOW(), %s, %s, %s)
                        """, [exercise_id, lesson_id, user_id])

                        # Check if all exercises in the lesson are completed
                        cursor.execute("""
                            SELECT COUNT(*) FROM courses_exercise WHERE lesson_id = %s
                        """, [lesson_id])
                        total_exercises = cursor.fetchone()[0]

                        cursor.execute("""
                            SELECT COUNT(*) FROM courses_userprogress WHERE user_id = %s AND lesson_id = %s
                        """, [user_id, lesson_id])
                        completed_exercises = cursor.fetchone()[0]

                        if completed_exercises == total_exercises:

                            cursor.execute("""
                                UPDATE courses_userxp SET xp_points = xp_points + 20 WHERE user_id = %s
                            """, [user_id])

                    # Award XP for answering correctly
                    cursor.execute("UPDATE courses_userxp SET xp_points = xp_points + 10 WHERE user_id = %s", [user_id])

                    # Update user streak only if they answer correctly
                    update_user_streak(user_id)

            return JsonResponse({"correct": is_correct})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

def next_lesson(request, lesson_id):
    with connection.cursor() as cursor:
        # Fetch the next lesson based on ID order
        cursor.execute("SELECT lesson_id FROM courses_lesson WHERE lesson_id > %s ORDER BY lesson_id ASC LIMIT 1", [lesson_id])
        next_lesson = cursor.fetchone()

    if next_lesson:
        return redirect(f'/lesson/{next_lesson[0]}/')
    else:
        return redirect('/dashboard/')

def update_user_streak(user_id):
    """Increment streak_days when the user logs in and performs any action."""
    today = date.today()

    with connection.cursor() as cursor:
        # Fetch last active date and current streak
        cursor.execute("""
            SELECT streak_days, last_xp_update
            FROM courses_userxp 
            WHERE user_id = %s
        """, [user_id])
        user_data = cursor.fetchone()

        if user_data:
            streak_days, last_active_at = user_data

            if last_active_at is None:
                # First-time login or no recorded date
                new_streak = 1
            else:
                # Convert to date object if needed
                last_active_at = last_active_at.date()

                if last_active_at == today:
                    # Already logged in today → No streak change
                    return
                elif last_active_at == today - timedelta(days=1):
                    # Logged in yesterday → Increment streak
                    new_streak = streak_days + 1
                else:
                    # Missed a day → Reset streak
                    new_streak = 1

            # Update streak_days and last_active_at
            cursor.execute("""
                UPDATE courses_userxp 
                SET streak_days = %s, last_xp_update = %s 
                WHERE user_id = %s
            """, [new_streak, today, user_id])

def leaderboard_view(request):
    if "user_id" not in request.session:
        return redirect("login")  # Redirect if not logged in

    user_id = request.session["user_id"]
    DEMOTION_XP_THRESHOLD = 20  # Set demotion zone threshold

    with connection.cursor() as cursor:
        # Get the selected language of the user
        cursor.execute("""
            SELECT selected_language_id FROM courses_user WHERE user_id = %s
        """, [user_id])
        user_language = cursor.fetchone()

        if not user_language:
            return redirect("dashboard")  # Redirect if user has no selected language

        selected_language_id = user_language[0]

        # Fetch top 10 leaderboard
        cursor.execute("""
            SELECT u.username, x.xp_points, RANK() OVER (ORDER BY x.xp_points DESC) AS rank
            FROM courses_user u join courses_userxp x
			on u.user_id = x.user_id
            WHERE u.selected_language_id = %s
            AND x.xp_points >= %s 
            ORDER BY x.xp_points DESC
            LIMIT 10
        """, [selected_language_id, DEMOTION_XP_THRESHOLD])
        top_leaderboard = cursor.fetchall()

        # Fetch demotion zone (only users below XP threshold)
        cursor.execute("""
            SELECT u.username, x.xp_points, RANK() OVER (ORDER BY x.xp_points ASC) AS rank
            FROM courses_user u join courses_userxp x
            on u.user_id = x.user_id
            WHERE u.selected_language_id = %s
            AND x.xp_points < %s 
            ORDER BY x.xp_points ASC
            LIMIT 5
        """, [selected_language_id, DEMOTION_XP_THRESHOLD])
        demotion_zone = cursor.fetchall()

    context = {
        "top_leaderboard": top_leaderboard,
        "demotion_zone": demotion_zone,
    }

    return render(request, "leaderboard.html", context)

def profile_view(request):
    """Display user profile information."""
    if "user_id" not in request.session:
        return redirect("login")

    user_id = request.session["user_id"]

    with connection.cursor() as cursor:
        # Fetch user details
        cursor.execute("""
            SELECT u.username, u.created_at, u.selected_language_id, l.language_name, l.language_code
            FROM courses_user u
            JOIN courses_language l ON u.selected_language_id = l.language_id
            WHERE u.user_id = %s
        """, [user_id])
        user_data = cursor.fetchone()

        if not user_data:
            return redirect("login")  # If no data, re-login

        username, created_at, language_id, language_name, language_code = user_data

        # Fetch XP and Streak
        cursor.execute("""
            SELECT xp_points, streak_days FROM courses_userxp WHERE user_id = %s
        """, [user_id])
        xp_data = cursor.fetchone()
        xp_points, streak_days = xp_data if xp_data else (0, 0)

        cursor.execute("""
            SELECT u.user_id, 
                RANK() OVER (ORDER BY x.xp_points DESC) AS rank
            FROM courses_userxp x 
            JOIN courses_user u ON u.user_id = x.user_id
            WHERE u.selected_language_id = %s;
            """, [language_id])
        rank_data = {row[0]: row[1] for row in cursor.fetchall()}  # Store ranks for all users
        user_rank = rank_data.get(user_id, "N/A")  # Get current user's rank safely

    context = {
        "username": username,
        "created_at": created_at.strftime("%B %d, %Y"),
        "language_name": language_name,
        "flag_url": f"/static/flags/{language_code}.png",
        "xp_points": xp_points,
        "streak_days": streak_days,
        "user_rank": user_rank,
        "profile_initial": username[0].upper() if username else "?",
    }

    return render(request, "profile.html", context)

QUESTS = [
    {"id": 1, "title": "Complete 5 Lessons", "goal": 5, "xp_reward": 50},
    {"id": 2, "title": "Earn 500 XP", "goal": 500, "xp_reward": 100},
    {"id": 3, "title": "Maintain a 7-day streak", "goal": 7, "xp_reward": 75},
]

def quests_view(request):
    if "user_id" not in request.session:
        return redirect("login")

    user_id = request.session["user_id"]

    with connection.cursor() as cursor:
        # Count completed lessons
        cursor.execute("""
            SELECT COUNT(DISTINCT lesson_id) FROM courses_userprogress WHERE user_id = %s
        """, [user_id])
        completed_lessons = cursor.fetchone()[0]

        # Get user's XP and streak days
        cursor.execute("SELECT xp_points, streak_days FROM courses_userxp WHERE user_id = %s", [user_id])
        xp_data = cursor.fetchone()
        xp_points, streak_days = xp_data if xp_data else (0, 0)

    # Track quest progress dynamically
    user_quests = []
    for quest in QUESTS:
        if quest["id"] == 1:
            progress = completed_lessons
        elif quest["id"] == 2:
            progress = xp_points
        elif quest["id"] == 3:
            progress = streak_days
        else:
            progress = 0

        completed = progress >= quest["goal"]

        # Award XP automatically if quest is completed
        if completed:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE courses_userxp SET xp_points = xp_points + %s WHERE user_id = %s",
                    [quest["xp_reward"], user_id]
                )

        user_quests.append({
            **quest,
            "progress": progress,
            "completed": completed,
            "progress_percentage": (progress / quest["goal"]) * 100 if quest["goal"] > 0 else 0
        })

    context = {"quests": user_quests}
    return render(request, "quests.html", context)

def claim_quest_reward(request, quest_id):
    if "user_id" not in request.session:
        return JsonResponse({"error": "Not logged in"}, status=403)

    user_id = request.session["user_id"]

    # Find the quest
    quest = next((q for q in QUESTS if q["id"] == quest_id), None)
    if not quest:
        return JsonResponse({"error": "Quest not found"}, status=404)

    with connection.cursor() as cursor:
        # Fetch user's current progress
        cursor.execute("SELECT xp_points, streak_days FROM courses_userxp WHERE user_id = %s", [user_id])
        xp_data = cursor.fetchone()
        xp_points, streak_days = xp_data if xp_data else (0, 0)

        cursor.execute("""
            SELECT COUNT(DISTINCT lesson_id) FROM courses_userprogress WHERE user_id = %s
        """, [user_id])
        completed_lessons = cursor.fetchone()[0]

    # Check if the quest is completed
    if quest_id == 1 and completed_lessons < quest["goal"]:
        return JsonResponse({"error": "Quest not completed"}, status=400)
    if quest_id == 2 and xp_points < quest["goal"]:
        return JsonResponse({"error": "Quest not completed"}, status=400)
    if quest_id == 3 and streak_days < quest["goal"]:
        return JsonResponse({"error": "Quest not completed"}, status=400)

    # Award XP for completing the quest
    with connection.cursor() as cursor:
        cursor.execute("UPDATE courses_userxp SET xp_points = xp_points + %s WHERE user_id = %s", [quest["xp_reward"], user_id])

    return JsonResponse({"success": True, "message": "XP awarded!"})

def shop_view(request):
    return render(request, "shop.html")

def home_view(request):
    return render(request, "home.html")


from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Choice, Course, Enrollment, Learner, Submission


def course_list(request):
    courses = Course.objects.all().order_by("id")
    return render(request, "onlinecourse/course_list.html", {"courses": courses})


def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrolled = False
    if request.user.is_authenticated:
        enrolled = Enrollment.objects.filter(
            learner__user=request.user, course=course
        ).exists()
    return render(
        request,
        "onlinecourse/course_details_bootstrap.html",
        {"course": course, "enrolled": enrolled},
    )


@login_required
@require_POST
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    learner, _ = Learner.objects.get_or_create(
        user=request.user, defaults={"name": request.user.get_full_name()}
    )
    Enrollment.objects.get_or_create(learner=learner, course=course)
    messages.success(request, "You are enrolled in this course.")
    return redirect("onlinecourse:course_details", course_id=course.id)


def register(request):
    if request.user.is_authenticated:
        return redirect("onlinecourse:course_list")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "That username is already in use.")
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            Learner.objects.create(user=user, name=username)
            login(request, user)
            return redirect("onlinecourse:course_list")
    return render(request, "onlinecourse/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("onlinecourse:course_list")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("onlinecourse:course_list")
        messages.error(request, "Invalid username or password.")
    return render(request, "onlinecourse/login.html")


def logout_view(request):
    logout(request)
    return redirect("onlinecourse:course_list")


def extract_answers(request):
    """Return integer choice IDs from POST fields named choice_<id>."""
    selected_ids = []
    for key, value in request.POST.items():
        if key.startswith("choice"):
            try:
                selected_ids.append(int(value))
            except (TypeError, ValueError):
                continue
    return selected_ids


@login_required
@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.filter(
        learner__user=request.user, course=course
    ).first()
    if enrollment is None:
        return HttpResponseForbidden("You must be enrolled to submit the exam.")

    selected_ids = extract_answers(request)
    valid_choices = Choice.objects.filter(id__in=selected_ids, question__course=course)

    submission = Submission.objects.create(enrollment=enrollment)
    submission.choices.add(*valid_choices)

    return HttpResponseRedirect(
        reverse("onlinecourse:show_exam_result", args=(course.id, submission.id))
    )


@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__course=course,
        enrollment__learner__user=request.user,
    )
    selected_ids = set(submission.choices.values_list("id", flat=True))

    lessons = course.lesson_set.prefetch_related("question_set__choice_set")
    questions = []
    for lesson in lessons:
        questions.extend(lesson.question_set.all())

    total_score = sum(q.grade for q in questions)
    score = sum(q.grade for q in questions if q.is_get_score(selected_ids))
    grade = (score / total_score * 100) if total_score else 0

    return render(
        request,
        "onlinecourse/exam_result_bootstrap.html",
        {
            "course": course,
            "submission": submission,
            "lessons": lessons,
            "selected_ids": selected_ids,
            "grade": grade,
            "score": score,
            "total_score": total_score,
            "passed": grade >= 80,
        },
    )

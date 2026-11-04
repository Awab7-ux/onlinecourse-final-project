from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from onlinecourse.models import Choice, Course, Instructor, Lesson


class Command(BaseCommand):
    help = "Create sample course content and the development admin account."

    @transaction.atomic
    def handle(self, *args, **options):
        instructor, _ = Instructor.objects.get_or_create(
            name="Sample Instructor", defaults={"email": "instructor@example.com"}
        )
        course, _ = Course.objects.get_or_create(
            name="Introduction to Online Learning",
            defaults={"description": "A sample course with lessons and a multi-choice exam."},
        )
        course.instructors.add(instructor)

        for title, content in [
            ("Learning Online", "Explore the basics of online learning."),
            ("Assessment Basics", "Review assessments and feedback."),
        ]:
            lesson, _ = Lesson.objects.get_or_create(
                course=course, title=title, defaults={"content": content}
            )
            self._create_questions(lesson)

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin123")
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("Seed data ready. Admin: admin/admin123"))

    def _create_questions(self, lesson):
        if lesson.question_set.exists():
            return
        if lesson.title == "Learning Online":
            data = [
                ("Which are common benefits of online learning?", 50, [
                    ("Flexible access to course materials", True),
                    ("Learning from different locations", True),
                    ("No need to study or practice", False),
                ]),
                ("What should a learner do when a course topic is unclear?", 50, [
                    ("Review the lesson and ask for help", True),
                    ("Ignore the topic", False),
                ]),
            ]
        else:
            data = [
                ("Which actions can help prepare for an assessment?", 50, [
                    ("Review the lesson objectives", True),
                    ("Practice with sample questions", True),
                    ("Submit without reading the questions", False),
                    ("Check the assessment instructions", True),
                ]),
            ]
        for text, grade, choices in data:
            q = lesson.question_set.create(
                course=lesson.course, question_text=text, grade=grade
            )
            Choice.objects.bulk_create(
                [Choice(question=q, choice_text=t, is_correct=c) for t, c in choices]
            )

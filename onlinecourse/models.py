from django.conf import settings
from django.db import models


class Instructor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Learner(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learner_profile",
    )
    name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name or self.user.username


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructors = models.ManyToManyField(Instructor, blank=True)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["learner", "course"],
                name="unique_learner_course_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.learner} - {self.course}"


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    question_text = models.TextField()
    grade = models.IntegerField(default=50)

    def is_get_score(self, selected_ids):
        """Return True when the selected choices match this question's correct choices."""
        try:
            selected = {int(choice_id) for choice_id in selected_ids}
        except (TypeError, ValueError):
            selected = set()

        question_choice_ids = set(self.choice_set.values_list("id", flat=True))
        selected_for_question = selected.intersection(question_choice_ids)
        correct_ids = set(
            self.choice_set.filter(is_correct=True).values_list("id", flat=True)
        )
        return selected_for_question == correct_ids

    def __str__(self):
        return self.question_text[:80]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text


class Submission(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission {self.pk} - {self.enrollment}"

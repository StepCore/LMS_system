from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from materials.models import Course, Lesson


class LessonSerializer(ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class CourseSerializer(ModelSerializer):
    lesson_counter = SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True, source='lesson')

    def get_lesson_counter(self, course):
        return course.lesson.count()

    class Meta:
        model = Course
        fields = "__all__"

from rest_framework import serializers

from materials.models import Course, Lesson
from materials.validators import validate_youtube_only


class LessonSerializer(serializers.ModelSerializer):
    video_url = serializers.URLField(
        validators=[validate_youtube_only], required=False, allow_null=True
    )

    def validate(self, data):
        """Проверка, что пользователь может изменять только свои уроки"""
        if self.instance and self.context["request"].user != self.instance.owner:
            raise serializers.ValidationError("Вы можете изменять только свои уроки")
        return data

    def create(self, validated_data):
        """Автоматическое назначение владельца при создании"""
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    class Meta:
        model = Lesson
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    lesson_counter = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True, source="lesson")
    is_subscribed = serializers.SerializerMethodField()

    def get_lesson_counter(self, course):
        return course.lesson.count()

    def get_is_subscribed(self, course):
        """Проверяет, подписан ли текущий пользователь на курс"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return course.subscriptions.filter(user=request.user).exists()
        return False

    class Meta:
        model = Course
        fields = "__all__"

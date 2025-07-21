from rest_framework import serializers
from .models import Payment
from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer


class PaymentSerializer(serializers.ModelSerializer):
    # Сериализаторы для связанных полей (можно сделать более компактными)
    paid_course = CourseSerializer(read_only=True)
    paid_lesson = LessonSerializer(read_only=True)

    # ID полей для записи (write_only)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='paid_course',
        write_only=True,
        required=False,
        allow_null=True
    )
    lesson_id = serializers.PrimaryKeyRelatedField(
        queryset=Lesson.objects.all(),
        source='paid_lesson',
        write_only=True,
        required=False,
        allow_null=True
    )

    # Человекочитаемое отображение способа оплаты
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'payment_date',
            'paid_course', 'course_id',
            'paid_lesson', 'lesson_id',
            'amount',
            'payment_method',
            'payment_method_display'
        ]
        read_only_fields = ['user', 'payment_date']
        extra_kwargs = {
            'payment_method': {'write_only': True}
        }

    def validate(self, data):
        """Проверка, что указан либо курс, либо урок"""
        if not data.get('paid_course') and not data.get('paid_lesson'):
            raise serializers.ValidationError("Необходимо указать курс или урок")
        if data.get('paid_course') and data.get('paid_lesson'):
            raise serializers.ValidationError("Укажите только курс или только урок")
        return data

    def create(self, validated_data):
        """Автоматическое назначение текущего пользователя"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

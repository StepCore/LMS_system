import django_filters
from django_filters import DateFromToRangeFilter

from materials.models import Course, Lesson

from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    payment_date = DateFromToRangeFilter(
        field_name="payment_date", label="Диапазон дат"
    )
    course = django_filters.ModelChoiceFilter(
        field_name="paid_course", queryset=Course.objects.all(), label="Курс"
    )
    lesson = django_filters.ModelChoiceFilter(
        field_name="paid_lesson", queryset=Lesson.objects.all(), label="Урок"
    )
    payment_method = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_METHOD_CHOICES, label="Способ оплаты"
    )

    class Meta:
        model = Payment
        fields = ["payment_date", "course", "lesson", "payment_method"]

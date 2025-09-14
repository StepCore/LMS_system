from rest_framework.serializers import ValidationError

forbidden_words = ["youtube.com"]


def validate_youtube_only(value):
    if value:
        if not any(words in value.lower() for words in forbidden_words):
            raise ValidationError(f"Загружать видео можно только с youtube.com")

from rest_framework import serializers
from .models import Totalexperience


class Totalexperienceserializers(serializers.ModelSerializer):
    class Meta:
        model = Totalexperience
        fields = "__all__"

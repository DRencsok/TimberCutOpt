from django.conf import settings
from rest_framework import serializers

from cutopt.get_solver import SOLVERS


class PieceSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=200)
    length = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(default=1, min_value=1)
    section = serializers.CharField(max_length=50)


class SolveRequestSerializer(serializers.Serializer):
    pieces = PieceSerializer(many=True)
    stock_lengths = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        default=(2400, 3600, 4800, 6000),
        allow_empty=False,
    )
    kerf = serializers.IntegerField(min_value=0, default=3)
    solver = serializers.ChoiceField(choices=list(SOLVERS), default="greedy")
    time_limit = serializers.FloatField(
        min_value=0.01,
        default=10,
        max_value=settings.CUTOPT_MAX_TIME_LIMIT,
        help_text="Total seconds for the whole request, split equally between sections, only used by CP-SAT",
    )

    def validate_pieces(self, value):
        if not value:
            raise serializers.ValidationError("Your cut list is empty. Add at least one piece")
        return value

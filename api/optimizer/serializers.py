from django.conf import settings
from rest_framework import serializers

from cutopt.get_solver import SOLVERS


class PieceSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=200)
    length = serializers.IntegerField(min_value=1, max_value=20000)
    quantity = serializers.IntegerField(
        default=1, min_value=1, max_value=settings.CUTOPT_MAX_PIECES
    )
    section = serializers.CharField(max_length=50)


class SolveRequestSerializer(serializers.Serializer):
    pieces = PieceSerializer(many=True, max_length=settings.CUTOPT_MAX_PIECES)
    stock_lengths = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=20000),
        default=(2400, 3600, 4800, 6000),
        allow_empty=False,
        max_length=settings.CUTOPT_MAX_STOCK_COUNT,
    )
    kerf = serializers.IntegerField(min_value=0, default=3, max_value=20)
    solver = serializers.ChoiceField(choices=list(SOLVERS), default="greedy")
    time_limit = serializers.FloatField(
        min_value=0.01,
        default=10,
        max_value=settings.CUTOPT_MAX_TIME_LIMIT,
        help_text="Total seconds for the whole request, "
        "split equally between sections, only used by CP-SAT",
    )

    def validate_pieces(self, value):
        total = sum(piece["quantity"] for piece in value)
        if total > settings.CUTOPT_MAX_PIECES:
            raise serializers.ValidationError(
                f"Your cut list exceeded the maximum capacity of {settings.CUTOPT_MAX_PIECES}"
            )
        if not value:
            raise serializers.ValidationError("Your cut list is empty. Add at least one piece")
        return value


class CutSerializer(serializers.Serializer):
    label = serializers.CharField()
    length = serializers.IntegerField()


class BoardSerializer(serializers.Serializer):
    section = serializers.CharField()
    stock_length = serializers.IntegerField()
    cuts = CutSerializer(many=True)
    offcut = serializers.IntegerField()
    used_length = serializers.IntegerField()


class ShoppingListItemSerializer(serializers.Serializer):
    section = serializers.CharField()
    length = serializers.IntegerField()
    quantity = serializers.IntegerField()


class SummarySerializer(serializers.Serializer):
    board_count = serializers.IntegerField()
    stock_length_total = serializers.IntegerField()
    piece_length_total = serializers.IntegerField()
    waste = serializers.IntegerField()
    waste_percent = serializers.FloatField()


class SolveResponseSerializer(serializers.Serializer):
    solver = serializers.ChoiceField(choices=list(SOLVERS))
    boards = BoardSerializer(many=True)
    shopping_list = ShoppingListItemSerializer(many=True)
    summary = SummarySerializer()

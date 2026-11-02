from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cutopt.errors import CutOptError
from cutopt.get_solver import get_solver
from cutopt.io import stock_for_sections
from cutopt.metrics import Metrics
from cutopt.models import Piece, Problem

from .serializers import SolveRequestSerializer, SolveResponseSerializer


class SolveView(APIView):
    @extend_schema(
        summary="Optimise a cut list",
        request=SolveRequestSerializer,
        responses={200: SolveResponseSerializer, 400: OpenApiResponse(description="Invalid input")},
        examples=[
            OpenApiExample(
                "Garden shed",
                value={
                    "pieces": [
                        {
                            "label": "wall stud",
                            "length": 1950,
                            "quantity": 16,
                            "section": "47x100 C24",
                        },
                        {
                            "label": "nogging",
                            "length": 550,
                            "quantity": 12,
                            "section": "47x100 C24",
                        },
                        {
                            "label": "rafter",
                            "length": 2150,
                            "quantity": 7,
                            "section": "47x150 C24",
                        },
                    ],
                    "stock_lengths": [2400, 3600, 4800, 6000],
                    "kerf": 3,
                    "solver": "cp_sat",
                    "time_limit": 10,
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = SolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            pieces = tuple(Piece(**piece) for piece in data["pieces"])
            sections = {p.section for p in pieces}
            stocks = stock_for_sections(sections, data["stock_lengths"])
            problem = Problem(stock=stocks, kerf=data["kerf"], pieces=pieces)
            solver = get_solver(data["solver"])
            if data["solver"] == "cp_sat":
                time_limit = data["time_limit"] / len(sections)
                boards = solver(problem=problem, time_limit=time_limit)
            else:
                boards = solver(problem=problem)

            metrics = Metrics.from_boards(boards)
        except CutOptError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            shopping_list = []
            for (section, length), qty in sorted(metrics.shopping_list.items()):
                shopping_list.append({"section": section, "length": length, "quantity": qty})

            response = SolveResponseSerializer(
                {
                    "solver": data["solver"],
                    "boards": boards,
                    "shopping_list": shopping_list,
                    "summary": metrics,
                }
            )
            return Response(response.data)

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

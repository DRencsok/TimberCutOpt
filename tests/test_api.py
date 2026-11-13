import random
from time import perf_counter

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from cutopt.get_solver import SOLVERS

client = APIClient()
URL = reverse("solve")
HEALTH_URL = reverse("health")
FRONTEND = "https://app.example.com"


def test_shed_with_greedy_returns_plan():
    body = {
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
        "solver": "greedy",
    }
    response = client.post(URL, body, format="json")

    assert response.status_code == 200, response.json()
    assert response.json()["summary"]["board_count"] == 11
    assert response.json()["summary"]["waste"] == 3550


@pytest.mark.parametrize("solver", SOLVERS)
def test_every_solver_runs(solver):
    body = {
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
        "solver": solver,
    }
    response = client.post(URL, body, format="json")

    assert response.status_code == 200, response.json()


def test_defaults_are_applied():
    body = {
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
        ]
    }
    response = client.post(URL, body, format="json")

    assert response.status_code == 200, response.json()
    assert response.json()["solver"] == "greedy"


def test_response_has_all_keys():
    body = {
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
        ]
    }

    response = client.post(URL, body, format="json")

    board = response.json()["boards"][0]
    shopping_list = response.json()["shopping_list"][0]
    summary = response.json()["summary"]
    assert set(board) == {"section", "stock_length", "cuts", "used_length", "offcut"}
    assert set(board["cuts"][0]) == {"label", "length"}
    assert set(shopping_list) == {"section", "length", "quantity"}
    assert set(summary) == {
        "board_count",
        "stock_length_total",
        "piece_length_total",
        "waste",
        "waste_percent",
    }


def test_serializer_error_with_empty_pieces():
    body = {"pieces": []}
    response = client.post(URL, body, format="json")

    errors = response.json()
    assert response.status_code == 400, errors
    assert "pieces" in errors
    assert "empty" in errors["pieces"][0]


def test_length_0_fails():
    body = {
        "pieces": [
            {
                "label": "wall stud",
                "length": 0,
                "quantity": 16,
                "section": "47x100 C24",
            },
            {"label": "rafter", "length": 1450, "quantity": 7, "section": "47x150 C24"},
        ],
    }
    response = client.post(URL, body, format="json")

    errors = response.json()
    assert response.status_code == 400, errors
    assert "length" in errors["pieces"]["0"]


def test_detail_error():
    body = {
        "pieces": [
            {
                "label": "rafter",
                "length": 9000,
                "quantity": 2,
                "section": "47x100 C24",
            }
        ],
    }
    response = client.post(URL, body, format="json")

    errors = response.json()
    assert response.status_code == 400, errors
    assert "rafter" in errors["detail"]


@pytest.mark.slow
def test_time_limit_is_a_budget_for_the_whole_request():
    # 60 different random lengths per section: too hard for CP-SAT to prove optimal in 1s
    rng = random.Random(0)
    pieces = [
        {"label": "piece", "length": rng.randrange(300, 3001, 50), "section": section}
        for section in ("47x100 C24", "47x150 C24")
        for _ in range(60)
    ]
    body = {"pieces": pieces, "solver": "cp_sat", "time_limit": 2}

    start = perf_counter()
    response = client.post(URL, body, format="json")
    elapsed = perf_counter() - start

    assert response.status_code == 200, response.json()
    assert elapsed < 3, f"took {elapsed:.2f} s"
    assert elapsed > 1.5, f"took {elapsed:.2f} s"


def test_get_is_not_allowed():
    response = client.get(URL)
    assert response.status_code == 405


@override_settings(CORS_ALLOWED_ORIGINS=[FRONTEND])
def test_cors_allows_frontend_origin():
    # The preflight a browser sends before a JSON POST from another origin
    response = client.options(URL, HTTP_ORIGIN=FRONTEND, HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST")
    assert response["Access-Control-Allow-Origin"] == FRONTEND


@override_settings(CORS_ALLOWED_ORIGINS=[FRONTEND])
def test_cors_rejects_other_origin():
    response = client.options(
        URL, HTTP_ORIGIN="https://evil.example.com", HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST"
    )
    assert "Access-Control-Allow-Origin" not in response


def test_health_returns_ok():
    response = client.get(HEALTH_URL)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_is_not_throttled():
    for _ in range(25):
        response = client.get(HEALTH_URL)
        assert response.status_code == 200


def test_post_is_not_allowed():
    response = client.post(HEALTH_URL)
    assert response.status_code == 405

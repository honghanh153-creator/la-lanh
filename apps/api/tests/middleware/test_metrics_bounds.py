from app.observability.metrics import HTTP_REQUESTS, _method_label


def test_unrecognized_methods_have_one_bounded_label() -> None:
    before = len(HTTP_REQUESTS._metrics)
    for index in range(500):
        HTTP_REQUESTS.labels(_method_label(f"CUSTOM{index}"), "/v1/health", "405").inc()
    assert len(HTTP_REQUESTS._metrics) <= before + 1
    assert _method_label("POST") == "POST"
    assert _method_label("GET") == "GET"

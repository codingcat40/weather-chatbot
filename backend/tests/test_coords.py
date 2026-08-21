from utils.coords import extract_coordinates


def test_extracts_coordinates_with_space():
    assert extract_coordinates("weather at 40.7128, -74.0060") == (40.7128, -74.0060)


def test_extracts_coordinates_without_space():
    assert extract_coordinates("40.7,-74.0") == (40.7, -74.0)


def test_returns_none_for_plain_text():
    assert extract_coordinates("what's the weather in Tokyo") is None


def test_rejects_out_of_range_values():
    assert extract_coordinates("200.0, 300.0") is None


def test_rejects_numbers_without_decimal_point():
    assert extract_coordinates("in 20, 30 minutes") is None

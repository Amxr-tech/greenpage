import pytest

from greenpage.model import estimate, rating_for


def test_zero_bytes_is_zero():
    e = estimate(0)
    assert e.grams_co2e == 0
    assert e.rating == "A+"


def test_one_gigabyte_matches_swd_v4():
    # 0.3 kWh/GB total energy at the 494 g/kWh global grid.
    e = estimate(1_000_000_000)
    assert e.energy_kwh == pytest.approx(0.3)
    assert e.grams_co2e == pytest.approx(0.3 * 494)


def test_green_hosting_reduces_emissions():
    assert estimate(2_000_000, green_hosting=True).grams_co2e < estimate(2_000_000).grams_co2e


def test_scales_linearly():
    assert estimate(4_000_000).grams_co2e == pytest.approx(2 * estimate(2_000_000).grams_co2e)


def test_rejects_negative():
    with pytest.raises(ValueError):
        estimate(-1)


@pytest.mark.parametrize(
    ("grams", "label"),
    [(0.04, "A+"), (0.05, "A"), (0.1, "B"), (0.2, "C"), (0.25, "D"), (0.3, "E"), (0.5, "F")],
)
def test_ratings(grams, label):
    assert rating_for(grams) == label

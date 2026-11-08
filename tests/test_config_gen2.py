"""Generation-2 configuration model: power-based tier keys with aliases, BEN 2000 hall, hardening levels, MV sizing."""
import math, os, sys, pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config, TIER_GEOMETRY, TIER_ALIASES, HARDENING, canonical_tier, PRESETS


@pytest.mark.parametrize("old,new", list(TIER_ALIASES.items()))
def test_aliases_resolve_everywhere(old, new):
    assert canonical_tier(old) == new and canonical_tier(new) == new
    assert Config(tier=old).tier == new
    assert Config.from_dict({"tier": old, "it_kw": 100, "racks": 5}).tier == new
    assert Config.preset(old).tier == new
    assert Config.preset(old).to_dict() == Config.preset(new).to_dict()


def test_canonical_keys_are_the_only_geometry_keys():
    assert list(TIER_GEOMETRY) == ["ben5", "ben30", "ben150", "ben500", "ben2000"]
    assert not set(TIER_ALIASES) & set(TIER_GEOMETRY)
    for t in TIER_GEOMETRY:
        assert not PRESETS[t].validate(), (t, PRESETS[t].validate())


def test_ben2000_preset_valid_and_dlc_only():
    c = Config.preset("ben2000")
    assert not c.validate()
    assert c.cooling == "dlc_cdu" and c.generator is True
    d = c.derived()
    assert d["kind"] == "hall" and d["modules"] == 3 and d["rows"] == 4 and d["mv_service"] is True
    assert 800 <= c.it_kw <= 2000 and c.racks <= 48
    for cooling in ("rdhx_drycooler", "inrow_dx", "cabinet_dx"):
        c2 = Config.preset("ben2000"); c2.cooling = cooling
        assert any("dlc_cdu" in e for e in c2.validate()), cooling
    c3 = Config.preset("ben2000"); c3.controls_tier = "lite"
    assert c3.validate()
    assert d["controls_tier_resolved"] == "pro"


def test_ben2000_mv_sizing_numbers():
    d = Config.preset("ben2000", "ai_training", "hot_arid").derived()
    assert d["voltage"].startswith("12.47 kV")
    assert d["transformer_kva"] == 2500 and d["transformers_total"] == 2       # N+1 -> 2N transformer pair
    assert d["ups_modules"] == 2 and 1800 <= d["ups_kva_each"] <= 2000
    assert d["generators_total"] == 3 and d["generator_kw_each"] == 1250        # N+1 of 1,250 kW
    assert d["service_breaker_a"] in (2500, 3000, 4000)
    assert 60_000 <= d["gross_kg"] <= 200_000


def test_transformers_total_for_2n_and_n():
    c = Config.preset("ben2000", "healthcare")
    assert c.redundancy == "2N"
    assert c.derived()["transformers_total"] == 2 * math.ceil(c.derived()["total_kva"] / 2250)
    c.redundancy = "N"
    assert c.derived()["transformers_total"] == math.ceil(c.derived()["total_kva"] / 2250)
    c.it_kw = 2000; c.racks = 48
    assert not c.validate()
    assert c.derived()["transformers_total"] == 2 and c.redundancy == "N"   # 2 MW IT + cooling > one 2,500 kVA unit at 90 %
    c.redundancy = "2N"
    assert c.derived()["transformers_total"] == 4
    # small tiers have no MV service
    for t in ("ben5", "ben30", "ben150", "ben500"):
        d = Config.preset(t).derived()
        assert d["mv_service"] is False and d["transformers_total"] == 0 and d["transformer_kva"] == 0


@pytest.mark.parametrize("profile,climate,expect", [
    ("ai_inference", "temperate", "H1"), ("private_cloud", "coastal", "H2"), ("ai_training", "hot_arid", "H2"),
    ("disaster_recovery", "cold", "H2"), ("industrial_ot", "high_altitude", "H2"), ("healthcare", "hot_humid", "H2"),
    ("public_sector", "temperate", "H3"), ("public_sector", "coastal", "H3"),
])
def test_hardening_default_by_climate_and_profile(profile, climate, expect):
    c = Config.preset("ben150", profile, climate)
    assert c.hardening == expect
    assert c.derived()["hardening_recommended"] == expect
    c2 = Config.preset("ben150", profile, climate, "H1")
    assert c2.hardening == "H1" and c2.derived()["hardening_recommended"] == expect


def test_hardening_table_and_mass_adder():
    assert list(HARDENING) == ["H1", "H2", "H3"]
    base = Config.preset("ben500", "ai_inference", "temperate", "H1").derived()
    h2 = Config.preset("ben500", "ai_inference", "temperate", "H2").derived()
    h3 = Config.preset("ben500", "ai_inference", "temperate", "H3").derived()
    assert base["gross_kg"] < h2["gross_kg"] < h3["gross_kg"]
    assert h2["gross_kg"] - base["gross_kg"] == round(base["payload_kg"] + base["envelope_area_m2"] * 6.0) - base["payload_kg"] or abs((h2["gross_kg"] - base["gross_kg"]) - base["envelope_area_m2"] * 6.0) <= 1
    assert abs((h3["gross_kg"] - base["gross_kg"]) - base["envelope_area_m2"] * 48.0) <= 1
    assert h3["hardening_label"].startswith("H3") and "UL 752" in h3["hardening_rating"]
    bad = Config.preset("ben150"); bad.hardening = "H4"
    assert any("hardening" in e for e in bad.validate())


def test_pods_formula_follows_racks_and_modules():
    assert Config.preset("ben5").derived()["pods"] == 3
    for t in ("ben30", "ben150", "ben500", "ben2000"):
        c = Config.preset(t); d = c.derived()
        assert d["pods"] == c.racks * 2 + 2 * TIER_GEOMETRY[t]["modules"], t
    assert Config.preset("ben2000").derived()["pods"] == Config.preset("ben2000").racks * 2 + 6


def test_row_fit_for_four_rows():
    c = Config.preset("ben2000", "ai_inference"); d = c.derived()
    assert c.racks == 48 and d["rows"] == 4 and d["racks_per_row"] == 12
    assert d["row_fits"] and d["row_length_mm"] <= TIER_GEOMETRY["ben2000"]["int_l_m"] * 1000
    # single-row tiers report rows == 1 and racks_per_row == racks
    for t in ("ben30", "ben150", "ben500"):
        c = Config.preset(t); d = c.derived()
        assert d["rows"] == 1 and d["racks_per_row"] == c.racks
    # the per-row check is what validate() uses
    c = Config.preset("ben2000"); c.racks = 48; c.it_kw = 2000
    assert not c.validate()


def test_cli_accepts_alias_and_hardening():
    from ben_engine.config import main
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["--tier", "ben20", "--hardening", "H2"])
    assert rc == 0 and "BEN 150" in buf.getvalue() and "H2" in buf.getvalue()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["--tier", "ben2000", "--json"])
    assert rc == 0 and '"mv_service": true' in buf.getvalue()

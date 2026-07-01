import db_supabase as sb


def test_slugify():
    assert sb._slugify("Pepe the Frog!") == "pepe-the-frog"
    assert sb._slugify("  ") == "meme-offering"


def test_scripture_from_lore_and_desc():
    row = {"lore": "Temple lore.", "description": "Origin story.", "summary": "Short."}
    text = sb._scripture_from(row)
    assert "Temple lore." in text
    assert "Origin story." in text


def test_scripture_from_summary_only():
    row = {"summary": "Only summary."}
    assert sb._scripture_from(row) == "Only summary."


def test_cat_tiers_cover_common():
    assert sb.CAT_TIERS["frog"] == "Sacred"
    assert sb.CAT_TIERS["4chan"] == "Ancient"
from app.domains.tarot.knowledge import BOOK_SOURCES, all_cards


def test_deck_contains_78_unique_original_cards() -> None:
    cards = all_cards()

    assert len(cards) == 78
    assert len({card.id for card in cards}) == 78
    assert sum(card.arcana == "major" for card in cards) == 22
    assert sum(card.arcana == "minor" for card in cards) == 56
    assert all(card.title_vi and card.core and card.tension and card.resource for card in cards)


def test_source_registry_records_five_complementary_books_without_excerpts() -> None:
    assert len(BOOK_SOURCES) == 5
    assert {source.source_id for source in BOOK_SOURCES} == {
        "pollack-78-degrees",
        "greer-tarot-for-yourself",
        "burger-fiebig-spreads",
        "lipp-interactions",
        "wen-holistic-tarot",
    }
    assert all(source.allowed_uses and source.prohibited_uses for source in BOOK_SOURCES)
    assert all("excerpt" in source.prohibited_uses for source in BOOK_SOURCES)

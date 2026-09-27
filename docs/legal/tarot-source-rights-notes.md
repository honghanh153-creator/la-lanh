# Tarot source and rights notes

Checked 2026-09-27. This is a product/engineering record, not legal advice.

## Safe-use rule

The Tarot engine may use high-level methods learned from published works—such as preserving user
agency, giving spread positions distinct jobs, and reading card interactions—without storing or
reproducing the books' expression. Runtime content must be independently written and reviewable.

Prohibited material includes excerpts, paraphrases that track distinctive wording, book-specific
metaphors, card entries, named spreads, layouts, diagrams, exercises, worksheets, tables, case
studies, and illustrations. Owning a copy or listing a source does not grant ingestion or
redistribution rights.

## Launch bibliography and allowed concepts

| Source | Official page | Concepts allowed in methodology | Excluded from product corpus |
|---|---|---|---|
| Rachel Pollack, *Seventy-Eight Degrees of Wisdom* | https://redwheelweiser.com/book/seventy-eight-degrees-of-wisdom-9781578636655/ | archetypal depth; symbolic tension | text, metaphors, structure, illustrations |
| Mary K. Greer, *Tarot for Your Self* | https://www.simonandschuster.co.uk/books/Tarot-for-Your-Self/Mary-K-Greer/9781578636792 | self-reflection; reader agency | text, exercises, worksheets, spreads |
| Evelin Bürger & Johannes Fiebig, *The Complete Book of Tarot Spreads* | https://www.hachettebookgroup.com/titles/evelin-burger/complete-book-of-tarot-spreads/9781454910794/ | position discipline; spread intent | text, named spreads, layouts, diagrams |
| Deborah Lipp, *Tarot Interactions* | https://www.llewellyn.com/product.php?ean=9780738745206 | interaction; contrast; progression | text, pair meanings, examples, templates |
| Benebell Wen, *Holistic Tarot* | https://www.northatlanticbooks.com/shop/holistic-tarot/ | non-determinism; ethical reflection | text, card entries, tables, cases, spreads |

## Engineering enforcement

- `BOOK_SOURCES` records source ID, concepts, official URL, allowed uses, and prohibited uses.
- Runtime provenance lists only concept sources actually used by the reading.
- `pnpm tarot:audit` verifies source uniqueness and that every source has explicit use boundaries.
- Source additions require a rights review, an original-content review, a knowledge version bump,
  fixtures, and release evidence. “Add a book” never means scrape or paste it into the repository.
- Deck art is not included. The current UI uses original abstract card faces and typography.


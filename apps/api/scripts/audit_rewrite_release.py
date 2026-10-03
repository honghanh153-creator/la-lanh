from __future__ import annotations

import argparse
from pathlib import Path

from app.domains.content_rewrite.evaluation import evaluate_release, load_manifest, load_records
from app.domains.content_rewrite.registry import canonical_surface_registry

DEFAULT_MANIFEST = (
    Path(__file__).parents[1] / "tests" / "fixtures" / "content_rewrite" / "corpus_manifest.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit the fixed rewrite evaluation corpus.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--manifest-only", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    manifest = load_manifest(args.manifest)
    registered = canonical_surface_registry().surfaces
    corpus_surfaces = frozenset(segment.surface for segment in manifest.segments)
    if corpus_surfaces != registered:
        missing = sorted(surface.value for surface in registered - corpus_surfaces)
        extra = sorted(surface.value for surface in corpus_surfaces - registered)
        raise SystemExit(f"Corpus registry mismatch; missing={missing}, extra={extra}")
    if len(manifest.case_ids) != 670:
        raise SystemExit("Rewrite release corpus must contain exactly 670 fixed synthetic cases")
    if args.manifest_only:
        print(
            f"Rewrite corpus manifest passed: {len(manifest.case_ids)} synthetic cases, "
            f"{len(corpus_surfaces)} surfaces, version {manifest.version}."
        )
        return
    if args.results is None:
        raise SystemExit("--results is required unless --manifest-only is used")
    result = evaluate_release(manifest, load_records(args.results))
    for surface in result.surfaces:
        print(
            f"{surface.surface.value}: cases={surface.case_count}, "
            f"comprehension={surface.comprehension_rate:.1%}, "
            f"relevance={surface.relevance_rate:.1%}, "
            f"duplicates={surface.duplicate_frame_rate:.1%}, "
            f"gate_failures={surface.gate_failures}, passed={surface.passed}"
        )
    if not result.passed:
        raise SystemExit(f"Rewrite release blocked: {', '.join(result.findings)}")
    print(f"Rewrite release passed for corpus {result.corpus_version}.")


if __name__ == "__main__":
    main()

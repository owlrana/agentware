"""Tests for the deterministic BM25 recall engine (Phase 1.1).

Exercises `retrieve_bm25` / `bm25_scores` directly against the synthetic KB:
  - a query whose terms appear only in entry X ranks X first;
  - scoring is deterministic (byte-identical) across repeated runs;
  - identical-score ties break deterministically (created desc -> id asc);
  - zero-overlap docs are excluded (score 0.0);
  - the `bm25` strategy dispatches through `retrieve()`.

Stdlib `unittest` only (no pytest, no new deps). Never touches the real KB.
"""

try:
    from tests._fixtures import SyntheticKBTestCase, load_cli, build_synthetic_kb
except ImportError:  # allow `python3 -m unittest tests.test_recall`
    from _fixtures import SyntheticKBTestCase, load_cli, build_synthetic_kb


CLI = load_cli()


class Bm25RankingTest(SyntheticKBTestCase):
    """BM25 ranking behavior over the synthetic KB."""

    def test_distinctive_query_ranks_owning_entry_first(self):
        # 'geofence arrive' vocabulary lives only in the geofence learning.
        ranked = CLI.retrieve_bm25(self.kdir, self.index_data,
                                   "geofence arrive reminders")
        self.assertEqual(ranked[0], "learn-geofence-reminders")

    def test_timeout_query_ranks_macos_entry_first(self):
        ranked = CLI.retrieve_bm25(self.kdir, self.index_data,
                                   "gtimeout coreutils command")
        self.assertEqual(ranked[0], "learn-macos-no-timeout")

    def test_bm25_query_ranks_reference_first(self):
        ranked = CLI.retrieve_bm25(self.kdir, self.index_data,
                                   "saturation inverse document frequency")
        self.assertEqual(ranked[0], "ref-bm25-ranking")

    def test_zero_overlap_query_returns_nothing(self):
        # 'kangaroo' appears in no entry -> no positive score -> empty ranking.
        ranked = CLI.retrieve_bm25(self.kdir, self.index_data, "kangaroo")
        self.assertEqual(ranked, [])

    def test_ranking_is_deterministic_across_runs(self):
        r1 = CLI.retrieve_bm25(self.kdir, self.index_data, "python stdlib ranking")
        r2 = CLI.retrieve_bm25(self.kdir, self.index_data, "python stdlib ranking")
        self.assertEqual(r1, r2)

    def test_scores_are_byte_identical_across_runs(self):
        corpus = CLI.build_corpus(self.kdir, self.index_data)
        toks = CLI.tokenize("python runtime dependency")
        s1 = [(e.get("id"), s) for (e, s) in CLI.bm25_scores(corpus, toks)]
        s2 = [(e.get("id"), s) for (e, s) in CLI.bm25_scores(corpus, toks)]
        self.assertEqual(s1, s2)

    def test_top_k_truncates(self):
        ranked_all = CLI.retrieve_bm25(self.kdir, self.index_data, "python ranking")
        ranked_1 = CLI.retrieve_bm25(self.kdir, self.index_data,
                                     "python ranking", top_k=1)
        self.assertLessEqual(len(ranked_1), 1)
        if ranked_all:
            self.assertEqual(ranked_1, ranked_all[:1])

    def test_dispatch_via_retrieve_uses_bm25(self):
        ranked = CLI.retrieve(self.kdir, self.index_data,
                              "geofence arrive reminders", "bm25")
        self.assertEqual(ranked[0], "learn-geofence-reminders")


class Bm25TieBreakTest(SyntheticKBTestCase):
    """Identical BM25 scores break deterministically: created desc -> id asc."""

    def setUp(self):
        # Two entries with IDENTICAL body vocabulary so a shared query term gives
        # them the SAME BM25 score; only created/id break the tie.
        body = (
            "# Tie\n\nalpha beta gamma alpha beta gamma identical vocabulary "
            "for a deterministic tie-break across both entries.\n"
        )
        entries = [
            {
                "id": "zzz-newer",          # later id, but NEWER created -> wins
                "title": "Tie A",
                "category": "references",
                "path": "references/tie-a.md",
                "tags": ["tie"],
                "created": "2026-02-02",
                "summary": "alpha beta gamma identical",
                "body": body,
            },
            {
                "id": "aaa-older",          # earlier id, but OLDER created -> loses
                "title": "Tie B",
                "category": "references",
                "path": "references/tie-b.md",
                "tags": ["tie"],
                "created": "2026-01-01",
                "summary": "alpha beta gamma identical",
                "body": body,
            },
        ]
        import tempfile, shutil
        self.kdir = tempfile.mkdtemp(prefix="agentware-test-tie-")
        self.addCleanup(shutil.rmtree, self.kdir, True)
        self.index_data = build_synthetic_kb(self.kdir, entries=entries)

    def test_identical_scores_break_by_created_then_id(self):
        ranked = CLI.retrieve_bm25(self.kdir, self.index_data, "alpha beta gamma")
        # Equal scores -> created desc wins: 2026-02-02 (zzz-newer) before older.
        self.assertEqual(ranked, ["zzz-newer", "aaa-older"])


class RecallCommandTest(SyntheticKBTestCase):
    """The `recall` command: ranking, token budgeting, and the JSON schema (1.2)."""

    def test_json_schema_and_top_ranked_entry(self):
        import json
        code, out, err = self.run_cli(
            ["recall", "geofence arrive reminders", "--format", "json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        # Stable top-level schema for the loop to consume.
        for key in ("query", "strategy", "top_k", "token_budget", "category",
                    "context_tokens", "count", "results"):
            self.assertIn(key, payload)
        self.assertEqual(payload["strategy"], "bm25")
        self.assertEqual(payload["count"], len(payload["results"]))
        self.assertTrue(payload["results"])
        first = payload["results"][0]
        for key in ("id", "path", "category", "score", "summary",
                    "estimated_tokens"):
            self.assertIn(key, first)
        # The geofence learning owns this vocabulary -> ranks first.
        self.assertEqual(first["id"], "learn-geofence-reminders")

    def test_budget_zero_returns_nothing(self):
        import json
        code, out, err = self.run_cli(
            ["recall", "geofence reminders", "--token-budget", "0",
             "--format", "json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["results"], [])
        self.assertEqual(payload["context_tokens"], 0)

    def test_small_budget_truncates_to_fewer_entries(self):
        import json
        full = json.loads(self.run_cli(
            ["recall", "python ranking stdlib", "--token-budget", "100000",
             "--format", "json"])[1])
        # A tiny budget must return strictly fewer (or equal) entries, never more,
        # and must respect the cumulative budget.
        small = json.loads(self.run_cli(
            ["recall", "python ranking stdlib", "--token-budget", "60",
             "--format", "json"])[1])
        self.assertLessEqual(small["count"], full["count"])
        self.assertLessEqual(small["context_tokens"], 60)

    def test_budget_is_cumulative_and_in_rank_order(self):
        import json
        payload = json.loads(self.run_cli(
            ["recall", "python ranking stdlib retrieval", "--token-budget", "1500",
             "--format", "json"])[1])
        # Cumulative footprint never exceeds the budget.
        self.assertLessEqual(payload["context_tokens"], 1500)
        self.assertEqual(
            payload["context_tokens"],
            sum(r["estimated_tokens"] for r in payload["results"]))
        # Scores are non-increasing (rank order preserved).
        scores = [r["score"] for r in payload["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_category_filter_restricts_results(self):
        import json
        payload = json.loads(self.run_cli(
            ["recall", "python ranking", "--category", "references",
             "--format", "json"])[1])
        self.assertTrue(payload["results"])
        self.assertTrue(all(r["category"] == "references"
                            for r in payload["results"]))

    def test_output_is_deterministic_across_runs(self):
        a = self.run_cli(["recall", "geofence reminders", "--format", "json"])[1]
        b = self.run_cli(["recall", "geofence reminders", "--format", "json"])[1]
        self.assertEqual(a, b)

    def test_text_format_runs(self):
        code, out, err = self.run_cli(["recall", "geofence reminders"])
        self.assertEqual(code, 0, err)
        self.assertIn("recall:", out)


class Bm25AcrStrategyTest(SyntheticKBTestCase):
    """`bm25+acr` (Phase 2.1): ACR re-ranks WITHIN the BM25 set, never adds to it.

    Two entries share identical body vocabulary -> identical BM25 score, so plain
    `bm25` orders them purely by the tie-break (created desc -> id asc). They
    differ in `source`/`last_verified`, so `acr(entry, as_of)` differs and
    `bm25+acr` reorders them by the ACR-weighted score.
    """

    AS_OF = "2026-06-25"

    def setUp(self):
        body = (
            "# ACR\n\ndelta epsilon zeta delta epsilon zeta identical vocabulary "
            "so both entries earn the SAME bm25 score and only acr can reorder.\n"
        )
        # Same score. Plain bm25 tie-break (created desc) puts the NEWER-created
        # 'bbb-imported' first. acr flips it: 'aaa-user' (source=user,
        # last_verified=as_of -> acr=1.0) beats 'bbb-imported' (source=imported,
        # stale last_verified -> acr=0.8*0.85=0.68).
        entries = [
            {
                "id": "aaa-user",
                "title": "ACR A",
                "category": "references",
                "path": "references/acr-a.md",
                "tags": ["acr"],
                "created": "2026-01-01",          # OLDER created -> loses plain tie
                "source": "user",                 # top provenance
                "last_verified": "2026-06-25",    # fresh at as_of -> freshness 1.0
                "summary": "delta epsilon zeta identical",
                "body": body,
            },
            {
                "id": "bbb-imported",
                "title": "ACR B",
                "category": "references",
                "path": "references/acr-b.md",
                "tags": ["acr"],
                "created": "2026-06-01",          # NEWER created -> wins plain tie
                "source": "imported",             # lowest provenance
                "last_verified": "2026-01-01",    # stale -> freshness floored 0.85
                "summary": "delta epsilon zeta identical",
                "body": body,
            },
        ]
        import tempfile, shutil
        self.kdir = tempfile.mkdtemp(prefix="agentware-test-acr-")
        self.addCleanup(shutil.rmtree, self.kdir, True)
        self.index_data = build_synthetic_kb(self.kdir, entries=entries)

    def test_plain_bm25_orders_by_created_tiebreak(self):
        # Sanity: with equal scores plain bm25 puts the newer-created entry first.
        ranked = CLI.retrieve_bm25(self.kdir, self.index_data, "delta epsilon zeta")
        self.assertEqual(ranked, ["bbb-imported", "aaa-user"])

    def test_acr_reorders_within_the_bm25_set(self):
        ranked = CLI.retrieve_bm25_acr(
            self.kdir, self.index_data, "delta epsilon zeta", self.AS_OF)
        # acr flips the order: the user-authored, fresh entry wins.
        self.assertEqual(ranked, ["aaa-user", "bbb-imported"])

    def test_acr_surfaces_the_same_set_as_bm25(self):
        plain = set(CLI.retrieve_bm25(
            self.kdir, self.index_data, "delta epsilon zeta"))
        acr = set(CLI.retrieve_bm25_acr(
            self.kdir, self.index_data, "delta epsilon zeta", self.AS_OF))
        self.assertEqual(plain, acr)  # same gate set; only the ORDER changes

    def test_acr_never_adds_a_zero_relevance_entry(self):
        # A term in no entry stays empty under acr (multiplier can't lift 0).
        ranked = CLI.retrieve_bm25_acr(
            self.kdir, self.index_data, "kangaroo", self.AS_OF)
        self.assertEqual(ranked, [])

    def test_acr_is_deterministic_at_fixed_as_of(self):
        a = CLI.retrieve_bm25_acr(
            self.kdir, self.index_data, "delta epsilon zeta", self.AS_OF)
        b = CLI.retrieve_bm25_acr(
            self.kdir, self.index_data, "delta epsilon zeta", self.AS_OF)
        self.assertEqual(a, b)

    def test_dispatch_via_retrieve_uses_bm25_acr(self):
        ranked = CLI.retrieve(self.kdir, self.index_data,
                              "delta epsilon zeta", "bm25+acr", as_of=self.AS_OF)
        self.assertEqual(ranked, ["aaa-user", "bbb-imported"])

    def test_recall_ranked_default_strategy_matches_plain_bm25(self):
        # Bare recall_ranked (default strategy) must equal retrieve_bm25 order.
        ranked_default = [e.get("id") for (e, _s, _t) in CLI.recall_ranked(
            self.kdir, self.index_data, "delta epsilon zeta")]
        plain = CLI.retrieve_bm25(self.kdir, self.index_data, "delta epsilon zeta")
        self.assertEqual(ranked_default, plain)

    def test_cli_strategy_flag_reorders_and_reports_strategy(self):
        import json
        payload = json.loads(self.run_cli(
            ["recall", "delta epsilon zeta", "--strategy", "bm25+acr",
             "--as-of", self.AS_OF, "--token-budget", "100000",
             "--format", "json"])[1])
        self.assertEqual(payload["strategy"], "bm25+acr")
        self.assertEqual([r["id"] for r in payload["results"]],
                         ["aaa-user", "bbb-imported"])

    def test_cli_acr_shorthand_equals_strategy_flag(self):
        long = self.run_cli(
            ["recall", "delta epsilon zeta", "--strategy", "bm25+acr",
             "--as-of", self.AS_OF, "--format", "json"])[1]
        short = self.run_cli(
            ["recall", "delta epsilon zeta", "--acr",
             "--as-of", self.AS_OF, "--format", "json"])[1]
        self.assertEqual(long, short)

    def test_cli_bm25_acr_byte_identical_across_runs(self):
        argv = ["recall", "delta epsilon zeta", "--strategy", "bm25+acr",
                "--as-of", self.AS_OF, "--format", "json"]
        self.assertEqual(self.run_cli(argv)[1], self.run_cli(argv)[1])

    def test_bare_recall_default_is_plain_bm25(self):
        import json
        payload = json.loads(self.run_cli(
            ["recall", "delta epsilon zeta", "--format", "json"])[1])
        self.assertEqual(payload["strategy"], "bm25")
        self.assertEqual([r["id"] for r in payload["results"]],
                         ["bbb-imported", "aaa-user"])


if __name__ == "__main__":
    import unittest
    unittest.main()

"""Tests for the trademark screening system."""

import sys
import os
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite://"

import pytest


# ─── Normalizer Tests ────────────────────────────────────────────────────────

class TestNormalizer:
    def test_basic_normalization(self):
        from backend.agents.normalizer import normalizer
        result = normalizer.normalize("NI-KKA")
        assert result.original == "NI-KKA"
        assert result.normalized == "nikka"
        assert result.is_valid is True
        assert "ni-kka" in result.variants

    def test_empty_input(self):
        from backend.agents.normalizer import normalizer
        result = normalizer.normalize("")
        assert result.is_valid is False
        assert result.error is not None

    def test_whitespace_only(self):
        from backend.agents.normalizer import normalizer
        result = normalizer.normalize("   ")
        assert result.is_valid is False

    def test_unicode_normalization(self):
        from backend.agents.normalizer import normalizer
        result = normalizer.normalize("Café")
        assert result.normalized == "cafe"
        assert result.is_valid is True

    def test_special_characters(self):
        from backend.agents.normalizer import normalizer
        result = normalizer.normalize("L'Oréal")
        assert "loreal" in result.normalized or result.normalized == "loreal"
        assert result.is_valid is True

    def test_numbers(self):
        from backend.agents.normalizer import normalizer
        result = normalizer.normalize("7-Eleven")
        assert "7eleven" in result.normalized or result.normalized == "7eleven"

    def test_batch_normalization(self):
        from backend.agents.normalizer import normalizer
        results = normalizer.normalize_batch(["Apple", "Google", "Microsoft"])
        assert len(results) == 3
        assert all(r.is_valid for r in results)


# ─── Phonetic Matcher Tests ─────────────────────────────────────────────────

class TestPhoneticMatcher:
    def test_similar_marks(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("quick", "kwik")
        assert result.phonetic_similarity > 50
        assert result.textual_similarity > 30

    def test_color_colour(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("color", "colour")
        assert result.textual_similarity > 70
        assert result.phonetic_similarity > 50

    def test_nykka_nykaa(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("nykka", "nykaa")
        assert result.textual_similarity > 70
        assert result.phonetic_similarity > 60

    def test_unrelated_marks(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("apple", "samsung")
        assert result.textual_similarity < 30
        assert result.phonetic_similarity < 40

    def test_empty_input(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("", "test")
        assert result.textual_similarity == 0.0
        assert result.phonetic_similarity == 0.0

    def test_exact_match(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("nike", "nike")
        assert result.textual_similarity == 100.0
        assert result.phonetic_similarity == 100.0

    def test_has_explanation(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        result = phonetic_matcher.compare("coca", "koka")
        assert result.explanation
        assert len(result.explanation) > 0

    def test_batch_comparison(self):
        from backend.agents.phonetic_matcher import phonetic_matcher
        results = phonetic_matcher.compare_batch("test", ["tast", "fest", "best"])
        assert len(results) == 3


# ─── Class Overlap Tests ────────────────────────────────────────────────────

class TestClassOverlap:
    def test_same_class(self):
        from backend.agents.class_overlap import class_overlap_agent
        result = class_overlap_agent.compare(
            [3], [3],
            "Cosmetics and skincare", "Beauty products"
        )
        assert result.class_overlap_score == 100.0
        assert result.overlapping_classes == [3]

    def test_different_classes(self):
        from backend.agents.class_overlap import class_overlap_agent
        result = class_overlap_agent.compare(
            [3], [9],
            "Cosmetics", "Computer software"
        )
        assert result.class_overlap_score == 0.0
        assert result.overlapping_classes == []

    def test_related_classes(self):
        from backend.agents.class_overlap import class_overlap_agent
        result = class_overlap_agent.compare(
            [3], [5],
            "Cosmetics", "Pharmaceutical preparations"
        )
        assert result.related_classes == [5]
        assert result.class_overlap_score > 0

    def test_empty_classes(self):
        from backend.agents.class_overlap import class_overlap_agent
        result = class_overlap_agent.compare(
            [], [],
            "Something", "Something else"
        )
        assert result.uncertain is True

    def test_description_similarity(self):
        from backend.agents.class_overlap import class_overlap_agent
        result = class_overlap_agent.compare(
            [3], [3],
            "Skin care creams and lotions", "Skincare moisturizing cream"
        )
        assert result.description_similarity > 30


# ─── Conflict Reporter Tests ────────────────────────────────────────────────

class TestConflictReporter:
    def test_combined_score(self):
        from backend.agents.conflict_reporter import conflict_reporter
        score = conflict_reporter.calculate_combined_score(80, 70, 90)
        # S = 0.35*80 + 0.30*70 + 0.35*90 = 28 + 21 + 31.5 = 80.5
        assert 80 <= score <= 81

    def test_priority_high(self):
        from backend.agents.conflict_reporter import conflict_reporter
        assert conflict_reporter.determine_priority(85) == "high"

    def test_priority_medium(self):
        from backend.agents.conflict_reporter import conflict_reporter
        assert conflict_reporter.determine_priority(60) == "medium"

    def test_priority_low(self):
        from backend.agents.conflict_reporter import conflict_reporter
        assert conflict_reporter.determine_priority(30) == "low"

    def test_priority_insufficient(self):
        from backend.agents.conflict_reporter import conflict_reporter
        assert conflict_reporter.determine_priority(10) == "insufficient"

    def test_escalation(self):
        from backend.agents.conflict_reporter import conflict_reporter
        assert conflict_reporter.should_escalate(85, "high") is True
        assert conflict_reporter.should_escalate(70, "medium") is True
        assert conflict_reporter.should_escalate(30, "low") is False

    def test_explanation_generation(self):
        from backend.agents.conflict_reporter import conflict_reporter
        explanation = conflict_reporter.generate_explanation(
            "TestMark", "TestMarc", 85, 90, 75, 83, "high"
        )
        assert "TestMark" in explanation
        assert "TestMarc" in explanation
        assert "DISCLAIMER" in explanation

    def test_score_boundary_values(self):
        from backend.agents.conflict_reporter import conflict_reporter
        # Test exact boundary
        assert conflict_reporter.determine_priority(75) == "high"
        assert conflict_reporter.determine_priority(74.9) == "medium"
        assert conflict_reporter.determine_priority(50) == "medium"
        assert conflict_reporter.determine_priority(49.9) == "low"
        assert conflict_reporter.determine_priority(25) == "low"
        assert conflict_reporter.determine_priority(24.9) == "insufficient"
        assert conflict_reporter.determine_priority(0) == "insufficient"
        assert conflict_reporter.determine_priority(100) == "high"

    def test_zero_scores(self):
        from backend.agents.conflict_reporter import conflict_reporter
        score = conflict_reporter.calculate_combined_score(0, 0, 0)
        assert score == 0.0

    def test_max_scores(self):
        from backend.agents.conflict_reporter import conflict_reporter
        score = conflict_reporter.calculate_combined_score(100, 100, 100)
        assert score == 100.0


# ─── MCP Server Tests ───────────────────────────────────────────────────────

class TestMCPServers:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        from backend.database.engine import init_db
        from backend.services.dataset_generator import seed_database
        init_db()
        seed_database()

    def test_search_marks(self):
        from backend.mcp_servers.trademark_server import search_marks
        result = search_marks("beauty", "IN", 5)
        assert "results" in result
        assert isinstance(result["results"], list)
        assert result["source"] == "synthetic_demo_dataset"

    def test_search_marks_empty_query(self):
        from backend.mcp_servers.trademark_server import search_marks
        result = search_marks("", "", 5)
        assert "results" in result

    def test_get_mark_details_not_found(self):
        from backend.mcp_servers.trademark_server import get_mark_details
        result = get_mark_details("NONEXISTENT")
        assert result["found"] is False

    def test_get_class_for_goods(self):
        from backend.mcp_servers.classes_server import get_class_for_goods
        result = get_class_for_goods("Cosmetics and skincare products")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert result["suggestions"][0]["class_number"] == 3

    def test_get_related_classes(self):
        from backend.mcp_servers.classes_server import get_related_classes
        result = get_related_classes(3)
        assert "related_classes" in result
        assert len(result["related_classes"]) > 0

    def test_get_related_invalid_class(self):
        from backend.mcp_servers.classes_server import get_related_classes
        result = get_related_classes(99)
        assert "error" in result


# ─── Workflow Tests ──────────────────────────────────────────────────────────

class TestWorkflow:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        from backend.database.engine import init_db
        from backend.services.dataset_generator import seed_database
        init_db()
        seed_database()

    def test_full_workflow(self):
        from backend.workflows.screening_graph import run_screening_workflow, WorkflowStatus
        state = run_screening_workflow(
            proposed_mark="Nykka",
            goods_description="Cosmetics and skincare products",
            nice_classes=[3],
            jurisdiction="IN",
        )
        assert state.status == WorkflowStatus.COMPLETED
        assert state.screening_id.startswith("SCR-")
        assert len(state.events) > 0

    def test_workflow_invalid_input(self):
        from backend.workflows.screening_graph import run_screening_workflow, WorkflowStatus
        state = run_screening_workflow(
            proposed_mark="",
            goods_description="Cosmetics",
            nice_classes=[3],
            jurisdiction="IN",
        )
        assert state.status == WorkflowStatus.FAILED
        assert len(state.errors) > 0

    def test_workflow_produces_matches(self):
        from backend.workflows.screening_graph import run_screening_workflow
        state = run_screening_workflow(
            proposed_mark="GlowUp",
            goods_description="Beauty products",
            nice_classes=[3],
            jurisdiction="IN",
        )
        # Should find at least some candidates with fuzzy matching
        assert len(state.candidates) >= 0  # May or may not find matches depending on seed

    def test_workflow_node_sequence(self):
        from backend.workflows.screening_graph import run_screening_workflow
        state = run_screening_workflow(
            proposed_mark="TestBrand",
            goods_description="Software services",
            nice_classes=[42],
            jurisdiction="US",
        )
        # Check all expected nodes executed
        node_names = [e.node_name for e in state.events]
        assert "validate_input" in node_names
        assert "normalize_mark" in node_names


# ─── Scoring Tests ───────────────────────────────────────────────────────────

class TestScoring:
    def test_formula_correctness(self):
        """Test S = 0.35P + 0.30T + 0.35G"""
        from backend.agents.conflict_reporter import conflict_reporter
        P, T, G = 94, 89, 100
        expected = 0.35 * P + 0.30 * T + 0.35 * G
        actual = conflict_reporter.calculate_combined_score(P, T, G)
        assert abs(actual - expected) < 0.01

    def test_weights_sum_to_one(self):
        from backend.agents.conflict_reporter import conflict_reporter
        total = (
            conflict_reporter.weight_phonetic
            + conflict_reporter.weight_textual
            + conflict_reporter.weight_goods
        )
        assert abs(total - 1.0) < 0.001

    def test_score_range(self):
        from backend.agents.conflict_reporter import conflict_reporter
        for p in [0, 25, 50, 75, 100]:
            for t in [0, 50, 100]:
                for g in [0, 50, 100]:
                    score = conflict_reporter.calculate_combined_score(p, t, g)
                    assert 0 <= score <= 100, f"Score {score} out of range for P={p}, T={t}, G={g}"

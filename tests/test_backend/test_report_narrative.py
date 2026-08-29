import pytest
from app.services.report_narrative_service import (
    NarrativeServiceError,
    validate_live_narrative,
    validate_typed_claims,
)

EVIDENCE = {
    "allowed_claim_types": ["trend", "coverage", "reference"],
    "trends": {"direction": "stable"},
    "coverage": {"status": "available"},
    "reference_comparison": {"station_days": [{"status": "eligible"}]},
}


def test_typed_claim_allow_list_accepts_only_supported_evidence_blocks() -> None:
    narrative, claims = validate_typed_claims(
        [
            {"claim_type": "trend", "text": "The observed pattern remains broadly stable."},
            {"claim_type": "coverage", "text": "Coverage supports a cautious qualitative reading."},
            {"claim_type": "reference", "text": "Reference context remains advisory and limited."},
        ],
        EVIDENCE,
    )
    assert len(claims) == 3
    assert narrative.startswith("The observed pattern")


@pytest.mark.parametrize(
    "text",
    [
        "Coverage reached 90 percent.",
        "See https://example.com for details.",
        "Contact person@example.com for details.",
        "<strong>The pattern is stable.</strong>",
        "The device caused cleaner air.",
        "The system is compliant with the standard.",
        "The intervention provides a health benefit.",
    ],
)
def test_any_unsafe_live_sentence_is_rejected(text: str) -> None:
    with pytest.raises(NarrativeServiceError):
        validate_typed_claims(
            [
                {"claim_type": "trend", "text": text},
                {"claim_type": "coverage", "text": "Coverage supports a cautious reading."},
                {"claim_type": "reference", "text": "Reference context remains advisory."},
            ],
            EVIDENCE,
        )


def test_unsupported_or_missing_claim_evidence_rejects_whole_payload() -> None:
    with pytest.raises(NarrativeServiceError, match="narrative_claim_type_not_allowed"):
        validate_typed_claims(
            [
                {"claim_type": "causal", "text": "The observed pattern remains stable."},
                {"claim_type": "coverage", "text": "Coverage supports a cautious reading."},
                {"claim_type": "reference", "text": "Reference context remains advisory."},
            ],
            EVIDENCE,
        )


def test_live_narrative_requires_three_to_five_sentences() -> None:
    with pytest.raises(NarrativeServiceError):
        validate_live_narrative("The pattern remains stable.")


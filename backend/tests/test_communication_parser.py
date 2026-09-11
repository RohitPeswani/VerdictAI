"""
Test Suite for CommunicationLogParser & EntityExtractor — NLP Pipeline
Author: Achyut Pathak (AI/NLP Engineer — Evidence Parsing)
"""

import pytest

from backend.app.services.nlp.communication_parser import CommunicationLogParser
from backend.app.services.nlp.entity_extractor import EntityExtractor, ExtractionResult
from backend.app.services.parsers.base_parser import (
    AnomalyLevel,
    ClaimAlignment,
    ParsedEvidence,
)


# ═══════════════════════════════════════════════════════════════════
#  EntityExtractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestEntityExtractor:

    @pytest.fixture
    def extractor(self):
        return EntityExtractor()

    # ── Date extraction ──

    def test_extract_iso_date(self, extractor):
        result = extractor.extract_entities("Payment processed on 2026-08-20")
        date_entities = [e for e in result.entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1
        assert "2026-08-20" in date_entities[0].text

    def test_extract_full_date(self, extractor):
        result = extractor.extract_entities("Ordered on August 20, 2026")
        date_entities = [e for e in result.entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1

    def test_extract_abbreviated_date(self, extractor):
        result = extractor.extract_entities("Shipped on Aug 20, 2026")
        date_entities = [e for e in result.entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1

    def test_extract_slash_date(self, extractor):
        result = extractor.extract_entities("Invoice dated 08/20/2026")
        date_entities = [e for e in result.entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1

    # ── Money extraction ──

    def test_extract_dollar_amount(self, extractor):
        result = extractor.extract_entities("Charged $1,249.50 to your card")
        money_entities = [e for e in result.entities if e.entity_type == "MONEY"]
        assert len(money_entities) >= 1
        assert "$1,249.50" in money_entities[0].text

    def test_extract_currency_code_amount(self, extractor):
        result = extractor.extract_entities("Total: USD 500.00")
        money_entities = [e for e in result.entities if e.entity_type == "MONEY"]
        assert len(money_entities) >= 1

    # ── Order ID extraction ──

    def test_extract_order_id(self, extractor):
        result = extractor.extract_entities("Your Order #ORD-12345678 has been placed")
        order_entities = [e for e in result.entities if e.entity_type == "ORDER_ID"]
        assert len(order_entities) >= 1

    def test_extract_reference_id(self, extractor):
        result = extractor.extract_entities("Reference: REF-ABC123")
        order_entities = [e for e in result.entities if e.entity_type == "ORDER_ID"]
        assert len(order_entities) >= 1

    # ── Tracking number extraction ──

    def test_extract_tracking_number(self, extractor):
        result = extractor.extract_entities("Tracking #: 1Z999AA10123456784")
        tracking_entities = [e for e in result.entities if e.entity_type == "TRACKING_NUMBER"]
        assert len(tracking_entities) >= 1

    # ── Email extraction ──

    def test_extract_email(self, extractor):
        result = extractor.extract_entities("Contact us at support@merchant.com")
        email_entities = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(email_entities) >= 1
        assert email_entities[0].text == "support@merchant.com"

    # ── Phone extraction ──

    def test_extract_phone(self, extractor):
        result = extractor.extract_entities("Call us at (555) 123-4567")
        phone_entities = [e for e in result.entities if e.entity_type == "PHONE"]
        assert len(phone_entities) >= 1

    # ── Person name extraction ──

    def test_extract_person_name(self, extractor):
        result = extractor.extract_entities("Signed by John Smith at the door")
        person_entities = [e for e in result.entities if e.entity_type == "PERSON"]
        assert len(person_entities) >= 1
        assert "John Smith" in [e.text for e in person_entities]

    def test_filters_common_phrases(self, extractor):
        result = extractor.extract_entities("Dear Customer, Thank You for your purchase")
        person_entities = [e for e in result.entities if e.entity_type == "PERSON"]
        person_texts = [e.text for e in person_entities]
        assert "Dear Customer" not in person_texts
        assert "Thank You" not in person_texts

    # ── Multi-entity extraction ──

    def test_extract_multiple_entity_types(self, extractor):
        text = (
            "On August 20, 2026, a charge of $249.50 was processed for "
            "Order #ORD-12345678. Contact support@store.com for help."
        )
        result = extractor.extract_entities(text)
        types = result.entity_types_found
        assert "DATE" in types
        assert "MONEY" in types
        assert "ORDER_ID" in types
        assert "EMAIL" in types

    def test_empty_text(self, extractor):
        result = extractor.extract_entities("")
        assert result.entity_count == 0
        assert result.entities == []

    def test_none_like_text(self, extractor):
        result = extractor.extract_entities("   ")
        assert result.entity_count == 0

    def test_extract_specific_type(self, extractor):
        text = "Charged $100 on 2026-08-20"
        money_only = extractor.extract_specific_type(text, "MONEY")
        assert all(e.entity_type == "MONEY" for e in money_only)

    def test_to_dict_output(self, extractor):
        result = extractor.extract_entities("$100 on 2026-08-20")
        d = result.to_dict()
        assert "extracted_entities" in d
        assert "entity_count" in d
        assert "entity_types_found" in d


# ═══════════════════════════════════════════════════════════════════
#  CommunicationLogParser Tests
# ═══════════════════════════════════════════════════════════════════

class TestCommunicationLogParserValidation:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_validate_with_messages(self, parser):
        payload = {"messages": [{"sender": "Alice", "content": "Hello"}]}
        assert parser.validate(payload) is True

    def test_validate_with_transcript(self, parser):
        payload = {"transcript": "Alice: Hello\nBob: Hi"}
        assert parser.validate(payload) is True

    def test_validate_empty_payload(self, parser):
        assert parser.validate({}) is False

    def test_validate_empty_messages_list(self, parser):
        assert parser.validate({"messages": []}) is False

    def test_validate_empty_transcript(self, parser):
        assert parser.validate({"transcript": ""}) is False


class TestCommunicationLogParserParsing:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    @pytest.fixture
    def cardholder_merchant_exchange(self):
        """Typical cardholder-merchant dispute conversation."""
        return {
            "channel": "EMAIL",
            "messages": [
                {
                    "sender": "Alice Smith",
                    "role": "CARDHOLDER",
                    "timestamp": "2026-08-21T09:00:00",
                    "content": "I ordered a laptop on August 15, 2026 but never received it. "
                               "The tracking shows delivered but nobody was home. "
                               "I want a full refund of $1,249.50. Order #ORD-98765.",
                },
                {
                    "sender": "Apex Support",
                    "role": "MERCHANT",
                    "timestamp": "2026-08-21T14:00:00",
                    "content": "Thank you for contacting us. Our tracking records show the "
                               "package was delivered and signed by J. DOE on August 18. "
                               "Per our policy, we cannot issue a refund for delivered orders. "
                               "Please check with your neighbours.",
                },
                {
                    "sender": "Alice Smith",
                    "role": "CARDHOLDER",
                    "timestamp": "2026-08-22T10:00:00",
                    "content": "I did not sign for anything and J. DOE is not someone I know. "
                               "This is unacceptable. If you don't refund me, I will file a "
                               "complaint with the BBB and contact my lawyer.",
                },
            ],
        }

    @pytest.fixture
    def resolved_exchange(self):
        """Conversation that ends with a resolution."""
        return {
            "channel": "CHAT",
            "messages": [
                {
                    "sender": "Bob",
                    "role": "CARDHOLDER",
                    "content": "My item arrived damaged. I need a replacement.",
                },
                {
                    "sender": "Support Agent",
                    "role": "MERCHANT",
                    "content": "We apologize for the inconvenience. A replacement has been "
                               "shipped and a refund issued for the damaged item. "
                               "The issue is now resolved.",
                },
            ],
        }

    def test_parse_structured_messages(self, parser, cardholder_merchant_exchange):
        result = parser.parse(cardholder_merchant_exchange)
        assert isinstance(result, ParsedEvidence)
        assert result.parser_name == "CommunicationLogParser"
        assert result.structured_data["total_messages"] == 3
        assert result.structured_data["cardholder_message_count"] == 2
        assert result.structured_data["merchant_message_count"] == 1
        assert result.structured_data["channel"] == "EMAIL"

    def test_parse_raw_transcript(self, parser):
        payload = {
            "transcript": (
                "Customer: I never received my order. Please refund.\n"
                "Merchant Support: Let me check your tracking status.\n"
                "Customer: It's been 2 weeks and nothing arrived."
            ),
        }
        result = parser.parse(payload)
        assert result.structured_data["total_messages"] >= 2

    def test_parse_raises_on_empty(self, parser):
        with pytest.raises(ValueError, match="must contain"):
            parser.parse({})

    def test_entity_extraction_from_messages(self, parser, cardholder_merchant_exchange):
        result = parser.parse(cardholder_merchant_exchange)
        entity_types = [e.entity_type for e in result.extracted_entities]
        # Should find money, dates, order IDs from message content
        assert "MONEY" in entity_types  # $1,249.50
        assert "PARTICIPANT" in entity_types  # Alice Smith, Apex Support

    def test_participants_extracted(self, parser, cardholder_merchant_exchange):
        result = parser.parse(cardholder_merchant_exchange)
        assert "Alice Smith" in result.structured_data["participants"]
        assert "Apex Support" in result.structured_data["participants"]


class TestCommunicationLogParserKeywords:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_cardholder_keywords_detected(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "I never received my order. The item was not as described. "
                               "I want a refund. This is fraudulent.",
                },
            ],
        }
        result = parser.parse(payload)
        kw_hits = result.structured_data["cardholder_keyword_hits"]
        assert "never received" in kw_hits or "refund" in kw_hits
        assert len(kw_hits) > 0

    def test_merchant_keywords_detected(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Support",
                    "role": "MERCHANT",
                    "content": "The package was delivered and signed for. "
                               "Our tracking shows confirmation. "
                               "Per our terms and conditions, this is a final sale.",
                },
            ],
        }
        result = parser.parse(payload)
        kw_hits = result.structured_data["merchant_keyword_hits"]
        assert len(kw_hits) > 0


class TestCommunicationLogParserSentiment:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_negative_sentiment(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "I am furious and frustrated. This is terrible and "
                               "unacceptable service. I am disgusted.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.structured_data["sentiment_score"] < 0

    def test_positive_sentiment(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "Thank you so much! I really appreciate your help. "
                               "Great service, I am very happy and satisfied.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.structured_data["sentiment_score"] > 0

    def test_neutral_sentiment(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "I placed an order on Monday. The tracking number is XYZ123.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.structured_data["sentiment_score"] == 0.0


class TestCommunicationLogParserEscalation:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_escalation_detected(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "If you don't resolve this I will contact my lawyer "
                               "and file a lawsuit.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.structured_data["escalation_detected"] is True
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "ESCALATION_LANGUAGE" in anomaly_types

    def test_no_escalation_in_normal_conversation(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "Can you please help me with my order status?",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.structured_data["escalation_detected"] is False


class TestCommunicationLogParserResolution:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_resolution_detected(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Support",
                    "role": "MERCHANT",
                    "content": "We have resolved the issue and a refund issued to your account.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.structured_data["resolution_detected"] is True


class TestCommunicationLogParserAlignment:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_supports_cardholder(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "I never received my product. It was damaged. "
                               "I want a refund. Not as described. Fraudulent charge. "
                               "Unauthorized transaction. I did not order this.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.claim_alignment == ClaimAlignment.SUPPORTS_CARDHOLDER

    def test_supports_merchant_with_resolution(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Support",
                    "role": "MERCHANT",
                    "content": "The package was delivered and tracking confirmed. "
                               "Signed by recipient. Proof of delivery attached. "
                               "The issue has been resolved and a replacement sent. "
                               "Per our policy and terms, this was confirmed.",
                },
            ],
        }
        result = parser.parse(payload)
        assert result.claim_alignment in (
            ClaimAlignment.SUPPORTS_MERCHANT, ClaimAlignment.NEUTRAL
        )

    def test_neutral_balanced_conversation(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "I would like to return this item for a refund.",
                },
                {
                    "sender": "Support",
                    "role": "MERCHANT",
                    "content": "The package was delivered and signed for. "
                               "Per our policy, confirmed delivery.",
                },
            ],
        }
        result = parser.parse(payload)
        # Balanced keywords should yield NEUTRAL
        assert result.claim_alignment in (
            ClaimAlignment.NEUTRAL, ClaimAlignment.SUPPORTS_CARDHOLDER,
            ClaimAlignment.SUPPORTS_MERCHANT,
        )


class TestCommunicationLogParserAnomalies:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_one_sided_communication_anomaly(self, parser):
        payload = {
            "messages": [
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Hello"},
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Anyone there?"},
            ],
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "ONE_SIDED_COMMUNICATION" in anomaly_types

    def test_empty_message_anomaly(self, parser):
        payload = {
            "messages": [
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Hello"},
                {"sender": "Support", "role": "MERCHANT", "content": ""},
            ],
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "EMPTY_MESSAGES" in anomaly_types

    def test_highly_negative_sentiment_anomaly(self, parser):
        payload = {
            "messages": [
                {
                    "sender": "Customer",
                    "role": "CARDHOLDER",
                    "content": "Terrible awful horrible disgusted outraged furious "
                               "frustrated disappointed ridiculous pathetic",
                },
            ],
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "HIGHLY_NEGATIVE_SENTIMENT" in anomaly_types


class TestCommunicationLogParserConfidence:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_multi_party_higher_confidence(self, parser):
        payload = {
            "messages": [
                {"sender": "Customer", "role": "CARDHOLDER", "content": "I have an issue"},
                {"sender": "Support", "role": "MERCHANT", "content": "Let me help"},
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Thank you"},
                {"sender": "Support", "role": "MERCHANT", "content": "You're welcome"},
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Issue resolved"},
            ],
        }
        result = parser.parse(payload)
        assert result.confidence_score >= 0.85

    def test_single_message_lower_confidence(self, parser):
        payload = {
            "messages": [
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Help me"},
            ],
        }
        result = parser.parse(payload)
        assert result.confidence_score < 0.85


class TestCommunicationLogParserEdgeCases:

    @pytest.fixture
    def parser(self):
        return CommunicationLogParser()

    def test_parser_name(self, parser):
        assert parser.parser_name == "CommunicationLogParser"

    def test_transcript_segmentation(self, parser):
        payload = {
            "transcript": (
                "Alice: I need help with my order\n"
                "Bob: Sure, what's the issue?\n"
                "Alice: It never arrived"
            ),
        }
        result = parser.parse(payload)
        assert result.structured_data["total_messages"] >= 2

    def test_unsegmentable_transcript(self, parser):
        payload = {
            "transcript": "Just a block of text with no clear sender markers.",
        }
        result = parser.parse(payload)
        assert result.structured_data["total_messages"] >= 1

    def test_nlp_entities_dict_output(self, parser):
        payload = {
            "messages": [
                {"sender": "Customer", "role": "CARDHOLDER", "content": "Charged $100"},
            ],
        }
        result = parser.parse(payload)
        nlp_dict = result.to_nlp_entities_dict()
        assert "extracted_entities" in nlp_dict
        assert "claim_alignment" in nlp_dict

    def test_metadata_contains_channel(self, parser):
        payload = {
            "channel": "CHAT",
            "messages": [
                {"sender": "User", "role": "CARDHOLDER", "content": "Hello"},
            ],
        }
        result = parser.parse(payload)
        assert result.metadata["channel"] == "CHAT"

    def test_raw_text_content_set(self, parser):
        payload = {
            "messages": [
                {"sender": "Alice", "role": "CARDHOLDER", "content": "Test message"},
            ],
        }
        result = parser.parse(payload)
        assert result.raw_text_content is not None
        assert "Alice" in result.raw_text_content
        assert "Test message" in result.raw_text_content

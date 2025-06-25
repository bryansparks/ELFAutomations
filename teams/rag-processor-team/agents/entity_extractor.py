"""
Entity Extractor Agent
Extracts entities and relationships based on document type and schema.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from elf_automations.shared.utils import get_supabase_client
from elf_automations.shared.utils.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class EntityExtractorAgent:
    """Agent responsible for extracting entities and relationships from documents"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.llm = LLMFactory.create_llm(
            provider="openai", model="gpt-4", temperature=0.1, enable_fallback=True
        )
        self.name = "entity_extractor"
        self.role = "Entity Extractor"
        self.backstory = (
            "A detail-oriented analyst who finds every important piece of information"
        )

    async def extract(
        self, content: str, schema: Dict[str, Any], document_type: str
    ) -> Dict[str, Any]:
        """Extract entities and relationships based on schema"""
        try:
            # Get extraction configuration
            extraction_config = schema.get("extraction_config", {})
            entity_types = schema.get("entity_types", [])
            relationship_types = schema.get("relationship_types", [])

            # Build extraction prompt
            prompt = self._build_extraction_prompt(
                content,
                document_type,
                entity_types,
                relationship_types,
                extraction_config,
            )

            # Extract with LLM
            response = await self.llm.ainvoke(prompt)
            extraction_result = self._parse_extraction_response(response.content)

            # Post-process and validate
            entities = self._process_entities(
                extraction_result.get("entities", []), entity_types
            )
            relationships = self._process_relationships(
                extraction_result.get("relationships", []), entities, relationship_types
            )

            # Apply confidence threshold
            confidence_threshold = extraction_config.get("confidence_threshold", 0.7)
            entities = [
                e for e in entities if e.get("confidence", 1.0) >= confidence_threshold
            ]
            relationships = [
                r
                for r in relationships
                if r.get("confidence", 1.0) >= confidence_threshold
            ]

            logger.info(
                f"Extracted {len(entities)} entities and {len(relationships)} relationships"
            )

            return {
                "entities": entities,
                "relationships": relationships,
                "metadata": {
                    "extraction_model": extraction_config.get("llm_model", "gpt-4"),
                    "confidence_threshold": confidence_threshold,
                    "document_type": document_type,
                },
            }

        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            return {"entities": [], "relationships": [], "error": str(e)}

    def _build_extraction_prompt(
        self,
        content: str,
        document_type: str,
        entity_types: List[str],
        relationship_types: List[str],
        config: Dict[str, Any],
    ) -> str:
        """Build extraction prompt based on document type"""

        # Use custom template if provided
        template = config.get("extraction_prompt_template")
        if template:
            return template.format(
                content=content,
                entity_types=", ".join(entity_types),
                relationship_types=", ".join(relationship_types),
            )

        # Build default prompt
        prompt = f"""Extract entities and relationships from this {document_type} document.

Entity types to extract:
{self._format_entity_types(entity_types, document_type)}

Relationship types to identify:
{self._format_relationship_types(relationship_types, document_type)}

Document content:
{content}

Provide extraction results in JSON format:
{{
    "entities": [
        {{
            "type": "entity_type",
            "value": "extracted value",
            "normalized_value": "standardized version",
            "properties": {{"key": "value based on entity type"}},
            "confidence": 0.95,
            "source_text": "exact text where found",
            "context": "surrounding context"
        }}
    ],
    "relationships": [
        {{
            "source_entity": "entity value",
            "source_type": "entity type",
            "target_entity": "entity value",
            "target_type": "entity type",
            "relationship_type": "type",
            "properties": {{"key": "value"}},
            "confidence": 0.9,
            "source_text": "text indicating relationship"
        }}
    ]
}}

Guidelines:
1. Extract ALL instances of the specified entity types
2. Normalize values (e.g., dates to ISO format, names to proper case)
3. Include confidence scores based on clarity and context
4. Capture relationships only between extracted entities
5. Include relevant properties for each entity type
"""

        return prompt

    def _format_entity_types(self, entity_types: List[str], document_type: str) -> str:
        """Format entity types with descriptions"""
        descriptions = {
            # Contract entities
            "party": "- party: Legal entities entering the agreement (companies, individuals)",
            "jurisdiction": "- jurisdiction: Legal jurisdictions governing the contract",
            "term": "- term: Key contractual terms and conditions",
            "obligation": "- obligation: Duties and responsibilities of parties",
            "date": "- date: Important dates (effective, expiration, deadlines)",
            "monetary_amount": "- monetary_amount: Financial values and payment terms",
            # Invoice entities
            "vendor": "- vendor: Selling/billing organization",
            "customer": "- customer: Buying/billed organization",
            "line_item": "- line_item: Individual products or services",
            "product": "- product: Specific products being invoiced",
            "service": "- service: Services being billed",
            # Technical doc entities
            "component": "- component: System components or modules",
            "system": "- system: Overall systems or applications",
            "requirement": "- requirement: Technical or functional requirements",
            "procedure": "- procedure: Step-by-step procedures or processes",
            "concept": "- concept: Technical concepts or terminology",
            "version": "- version: Version numbers or release information",
            # Generic entities
            "person": "- person: Individual people mentioned",
            "organization": "- organization: Companies, institutions, agencies",
            "location": "- location: Geographic locations",
            "amount": "- amount: Numeric values with units",
        }

        return "\n".join([descriptions.get(et, f"- {et}: {et}") for et in entity_types])

    def _format_relationship_types(
        self, relationship_types: List[str], document_type: str
    ) -> str:
        """Format relationship types with descriptions"""
        descriptions = {
            # Contract relationships
            "PARTY_TO": "- PARTY_TO: Entity is a party to the contract",
            "GOVERNED_BY": "- GOVERNED_BY: Contract/entity governed by jurisdiction",
            "CONTAINS_OBLIGATION": "- CONTAINS_OBLIGATION: Document contains obligation",
            "EXPIRES_ON": "- EXPIRES_ON: Entity expires on date",
            # Invoice relationships
            "BILLED_TO": "- BILLED_TO: Invoice billed to customer",
            "PROVIDED_BY": "- PROVIDED_BY: Service/product provided by vendor",
            "CONTAINS": "- CONTAINS: Invoice contains line item",
            # Technical relationships
            "DESCRIBES": "- DESCRIBES: Document describes component/system",
            "DEPENDS_ON": "- DEPENDS_ON: Component depends on another",
            "IMPLEMENTS": "- IMPLEMENTS: Component implements requirement",
            "PREREQUISITE_OF": "- PREREQUISITE_OF: Is prerequisite of another",
            # Generic relationships
            "REFERENCES": "- REFERENCES: Entity references another",
            "RELATED_TO": "- RELATED_TO: General relationship",
            "MENTIONS": "- MENTIONS: Document mentions entity",
        }

        return "\n".join(
            [descriptions.get(rt, f"- {rt}: {rt}") for rt in relationship_types]
        )

    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM extraction response"""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)

        except Exception as e:
            logger.error(f"Error parsing extraction response: {str(e)}")

        return {"entities": [], "relationships": []}

    def _process_entities(
        self, raw_entities: List[Dict[str, Any]], allowed_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Process and validate extracted entities"""
        processed = []

        for entity in raw_entities:
            # Skip if not allowed type
            if entity.get("type") not in allowed_types:
                continue

            # Normalize based on type
            normalized = self._normalize_entity(entity)

            # Add to processed list
            processed.append(normalized)

        # Deduplicate
        return self._deduplicate_entities(processed)

    def _normalize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize entity based on type"""
        entity_type = entity.get("type", "")
        value = entity.get("value", "")

        # Date normalization
        if entity_type in ["date", "expiration_date", "effective_date"]:
            normalized_value = self._normalize_date(value)
            entity["normalized_value"] = normalized_value
            if "properties" not in entity:
                entity["properties"] = {}
            entity["properties"]["original_format"] = value

        # Monetary amount normalization
        elif entity_type in ["monetary_amount", "amount"]:
            amount, currency = self._normalize_amount(value)
            entity["normalized_value"] = f"{amount} {currency}"
            if "properties" not in entity:
                entity["properties"] = {}
            entity["properties"]["amount"] = amount
            entity["properties"]["currency"] = currency

        # Organization/party normalization
        elif entity_type in ["party", "vendor", "customer", "organization"]:
            entity["normalized_value"] = self._normalize_organization(value)

        # Default normalization
        else:
            entity["normalized_value"] = entity.get("normalized_value", value.strip())

        # Ensure required fields
        entity["confidence"] = entity.get("confidence", 1.0)
        entity["properties"] = entity.get("properties", {})

        return entity

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to ISO format"""
        # Common date patterns
        patterns = [
            (r"(\d{1,2})/(\d{1,2})/(\d{4})", "%m/%d/%Y"),
            (r"(\d{1,2})-(\d{1,2})-(\d{4})", "%m-%d-%Y"),
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
            (r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", "%B %d, %Y"),
        ]

        for pattern, format_str in patterns:
            try:
                match = re.match(pattern, date_str.strip())
                if match:
                    dt = datetime.strptime(match.group(0), format_str)
                    return dt.date().isoformat()
            except:
                continue

        return date_str

    def _normalize_amount(self, amount_str: str) -> Tuple[float, str]:
        """Extract numeric amount and currency"""
        # Remove commas and spaces
        cleaned = amount_str.replace(",", "").strip()

        # Common currency patterns
        currency_symbols = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}

        # Try to extract amount and currency
        amount = 0.0
        currency = "USD"

        for symbol, curr in currency_symbols.items():
            if symbol in cleaned:
                currency = curr
                cleaned = cleaned.replace(symbol, "").strip()
                break

        # Extract numeric value
        match = re.search(r"[\d,]+\.?\d*", cleaned)
        if match:
            try:
                amount = float(match.group(0))
            except:
                pass

        return amount, currency

    def _normalize_organization(self, org_name: str) -> str:
        """Normalize organization name"""
        # Remove common suffixes
        suffixes = ["Inc.", "Inc", "LLC", "Ltd.", "Ltd", "Corp.", "Corp", "Co.", "Co"]
        normalized = org_name.strip()

        for suffix in suffixes:
            if normalized.endswith(f" {suffix}"):
                normalized = normalized[: -len(suffix) - 1].strip()

        return normalized

    def _deduplicate_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate entities"""
        seen = set()
        unique = []

        for entity in entities:
            # Create unique key
            key = (entity["type"], entity.get("normalized_value", entity["value"]))

            if key not in seen:
                seen.add(key)
                unique.append(entity)
            else:
                # Merge properties if duplicate
                for existing in unique:
                    if (
                        existing["type"],
                        existing.get("normalized_value", existing["value"]),
                    ) == key:
                        # Merge properties
                        existing["properties"].update(entity.get("properties", {}))
                        # Keep higher confidence
                        existing["confidence"] = max(
                            existing["confidence"], entity.get("confidence", 0)
                        )
                        break

        return unique

    def _process_relationships(
        self,
        raw_relationships: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        allowed_types: List[str],
    ) -> List[Dict[str, Any]]:
        """Process and validate relationships"""
        processed = []

        # Create entity lookup
        entity_lookup = {
            entity.get("normalized_value", entity["value"]): entity
            for entity in entities
        }

        for rel in raw_relationships:
            # Skip if not allowed type
            if rel.get("relationship_type") not in allowed_types:
                continue

            # Verify entities exist
            source = rel.get("source_entity")
            target = rel.get("target_entity")

            if source in entity_lookup and target in entity_lookup:
                # Add entity type information
                rel["source_type"] = entity_lookup[source]["type"]
                rel["target_type"] = entity_lookup[target]["type"]

                # Ensure required fields
                rel["confidence"] = rel.get("confidence", 1.0)
                rel["properties"] = rel.get("properties", {})

                processed.append(rel)

        return processed

    async def store_entities(
        self,
        document_id: str,
        tenant_id: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ) -> None:
        """Store extracted entities and relationships in database"""
        try:
            # Store entities
            entity_id_map = {}
            for entity in entities:
                # Insert entity
                result = (
                    self.supabase.table("rag_extracted_entities")
                    .insert(
                        {
                            "tenant_id": tenant_id,
                            "document_id": document_id,
                            "entity_type": entity["type"],
                            "entity_value": entity["value"],
                            "normalized_value": entity.get(
                                "normalized_value", entity["value"]
                            ),
                            "properties": entity.get("properties", {}),
                            "confidence": entity.get("confidence", 1.0),
                            "extraction_method": "llm",
                            "source_text": entity.get("source_text", ""),
                        }
                    )
                    .execute()
                )

                if result.data:
                    entity_id_map[entity["value"]] = result.data[0]["id"]

            # Store relationships
            for rel in relationships:
                source_id = entity_id_map.get(rel["source_entity"])
                target_id = entity_id_map.get(rel["target_entity"])

                if source_id and target_id:
                    self.supabase.table("rag_entity_relationships").insert(
                        {
                            "tenant_id": tenant_id,
                            "document_id": document_id,
                            "source_entity_id": source_id,
                            "target_entity_id": target_id,
                            "relationship_type": rel["relationship_type"],
                            "properties": rel.get("properties", {}),
                            "confidence": rel.get("confidence", 1.0),
                            "extraction_method": "llm",
                            "source_text": rel.get("source_text", ""),
                        }
                    ).execute()

            # Update extraction history
            self.supabase.table("rag_extraction_history").insert(
                {
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                    "extraction_type": "entities",
                    "items_extracted": len(entities),
                    "status": "completed",
                }
            ).execute()

            logger.info(
                f"Stored {len(entities)} entities and {len(relationships)} relationships"
            )

        except Exception as e:
            logger.error(f"Error storing entities: {str(e)}")
            raise

    async def extract_entities(self, *args, **kwargs):
        """Alias for extract method"""
        return await self.extract(*args, **kwargs)

    async def extract_relationships(
        self,
        entities: List[Dict[str, Any]],
        content: str,
        relationship_types: List[str],
    ) -> List[Dict[str, Any]]:
        """Extract relationships between already identified entities"""
        # This is handled in the main extract method
        # Provided as separate method for workflow compatibility
        return []

    async def normalize_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize a list of entities"""
        return [self._normalize_entity(e) for e in entities]

    async def store_extracted_data(self, *args, **kwargs):
        """Alias for store_entities method"""
        return await self.store_entities(*args, **kwargs)

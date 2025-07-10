"""
Document Classifier Agent
Identifies document types and selects appropriate processing strategies.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from elf_automations.shared.utils import get_supabase_client
from elf_automations.shared.utils.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class DocumentClassifierAgent:
    """Agent responsible for classifying documents and selecting processing strategies"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.llm = LLMFactory.create_llm(
            provider="openai", model="gpt-4", temperature=0.2, enable_fallback=True
        )
        self.name = "document_classifier"
        self.role = "Document Classifier"
        self.backstory = "An expert at recognizing document patterns and structures"

    async def classify(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Classify document type based on content and metadata"""
        try:
            # Get available document types from schema
            schemas_result = (
                self.supabase.table("rag_extraction_schemas")
                .select("document_type, display_name, description")
                .eq("is_active", True)
                .execute()
            )

            available_types = []
            if schemas_result.data:
                available_types = [
                    {
                        "type": schema["document_type"],
                        "name": schema["display_name"],
                        "description": schema["description"],
                    }
                    for schema in schemas_result.data
                ]

            # Build classification prompt
            prompt = self._build_classification_prompt(
                content, metadata, available_types
            )

            # Get LLM classification
            response = await self.llm.ainvoke(prompt)
            classification_result = self._parse_classification_response(
                response.content
            )

            # Store classification result
            if metadata.get("document_id"):
                self.supabase.table("rag_document_classifications").insert(
                    {
                        "document_id": metadata["document_id"],
                        "detected_type": classification_result["type"],
                        "confidence": classification_result["confidence"],
                        "alternatives": classification_result.get("alternatives", []),
                        "classification_method": "llm",
                        "model_used": "gpt-4",
                    }
                ).execute()

            logger.info(
                f"Classified document as {classification_result['type']} "
                f"with confidence {classification_result['confidence']}"
            )

            return classification_result

        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            # Default to generic document type
            return {
                "type": "generic",
                "confidence": 0.0,
                "alternatives": [],
                "error": str(e),
            }

    def _build_classification_prompt(
        self,
        content: str,
        metadata: Dict[str, Any],
        available_types: List[Dict[str, Any]],
    ) -> str:
        """Build prompt for document classification"""
        # Truncate content if too long
        max_content_length = 3000
        content_sample = (
            content[:max_content_length] + "..."
            if len(content) > max_content_length
            else content
        )

        types_description = "\n".join(
            [
                f"- {t['type']}: {t['name']} - {t['description']}"
                for t in available_types
            ]
        )

        prompt = f"""Classify the following document into one of these types:

{types_description}

Document metadata:
- Filename: {metadata.get('filename', 'unknown')}
- MIME type: {metadata.get('mime_type', 'unknown')}
- Size: {metadata.get('size_bytes', 0)} bytes

Document content (sample):
{content_sample}

Analyze the document and provide classification in JSON format:
{{
    "type": "detected_document_type",
    "confidence": 0.95,  // confidence score between 0 and 1
    "reasoning": "Brief explanation of why this type was chosen",
    "alternatives": [  // other possible types with lower confidence
        {{"type": "alternative_type", "confidence": 0.3}}
    ],
    "key_indicators": ["list", "of", "features", "that", "led", "to", "classification"]
}}

Focus on:
1. Document structure and formatting
2. Key terminology and language patterns
3. Presence of specific sections or fields
4. Overall purpose and context
"""

        return prompt

    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM classification response"""
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)

                # Validate required fields
                if "type" in result and "confidence" in result:
                    return result

            # Fallback parsing if JSON extraction fails
            logger.warning("Failed to parse JSON from classification response")
            return {"type": "generic", "confidence": 0.5, "alternatives": []}

        except Exception as e:
            logger.error(f"Error parsing classification response: {str(e)}")
            return {"type": "generic", "confidence": 0.0, "alternatives": []}

    async def get_extraction_schema(self, document_type: str) -> Dict[str, Any]:
        """Get extraction schema for document type"""
        try:
            # Get schema from database
            schema_result = (
                self.supabase.table("rag_extraction_schemas")
                .select("*")
                .eq("document_type", document_type)
                .eq("is_active", True)
                .single()
                .execute()
            )

            if schema_result.data:
                schema = schema_result.data
                return {
                    "document_type": schema["document_type"],
                    "entity_types": schema["entity_types"],
                    "relationship_types": schema["relationship_types"],
                    "extraction_config": schema["extraction_config"],
                    "chunking_strategy": schema["chunking_strategy"],
                    "graph_schema": schema["graph_schema"],
                }
            else:
                # Return generic schema if specific type not found
                logger.warning(
                    f"No schema found for type {document_type}, using generic"
                )
                return self._get_generic_schema()

        except Exception as e:
            logger.error(f"Error getting extraction schema: {str(e)}")
            return self._get_generic_schema()

    def _get_generic_schema(self) -> Dict[str, Any]:
        """Get generic extraction schema for unknown document types"""
        return {
            "document_type": "generic",
            "entity_types": [
                "term",
                "date",
                "person",
                "organization",
                "location",
                "amount",
            ],
            "relationship_types": ["MENTIONS", "REFERENCES", "RELATED_TO"],
            "extraction_config": {
                "llm_model": "gpt-4",
                "temperature": 0.1,
                "extraction_prompt_template": "Extract key entities and relationships from this document.",
                "confidence_threshold": 0.7,
            },
            "chunking_strategy": {
                "primary_strategy": "sliding_window",
                "chunk_size": 1000,
                "overlap": 200,
            },
            "graph_schema": {
                "node_labels": {
                    "term": "Term",
                    "person": "Person",
                    "organization": "Organization",
                }
            },
        }

    async def validate_classification(
        self, document_id: str, document_type: str, content: str
    ) -> Dict[str, Any]:
        """Validate classification by checking for expected patterns"""
        try:
            # Get expected patterns from schema
            schema = await self.get_extraction_schema(document_type)

            validation_prompt = f"""Validate if this document is correctly classified as '{document_type}'.

Expected characteristics for {document_type}:
- Entity types: {', '.join(schema['entity_types'])}
- Typical structure and patterns

Document sample:
{content[:1000]}

Provide validation result as JSON:
{{
    "is_valid": true/false,
    "confidence": 0.9,
    "issues": ["list of any issues found"],
    "suggestions": ["alternative classifications if not valid"]
}}"""

            response = await self.llm.ainvoke(validation_prompt)
            return self._parse_validation_response(response.content)

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {"is_valid": True, "confidence": 0.5}

    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response"""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)

        except Exception:
            pass

        return {"is_valid": True, "confidence": 0.5}

    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get document metadata from database"""
        try:
            result = (
                self.supabase.table("rag_documents")
                .select("*")
                .eq("id", document_id)
                .single()
                .execute()
            )

            if result.data:
                return result.data

        except Exception as e:
            logger.error(f"Error getting document metadata: {str(e)}")

        return {}

    async def update_classification(
        self, document_id: str, classification: Dict[str, Any]
    ) -> None:
        """Update document classification in database"""
        try:
            # Update document type
            self.supabase.table("rag_documents").update(
                {
                    "document_type_id": classification.get("type_id"),
                    "extracted_metadata": {"classification": classification},
                }
            ).eq("id", document_id).execute()

            logger.info(f"Updated classification for document {document_id}")

        except Exception as e:
            logger.error(f"Error updating classification: {str(e)}")

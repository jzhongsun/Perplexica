from typing import Dict, List
from fastapi import HTTPException
from .templates import TEMPLATES
from .schemas import PromptTemplate, PromptRequest, PromptResponse

class PromptService:
    """Service for managing and generating prompts."""

    def __init__(self):
        self.templates = {
            name: PromptTemplate(**template)
            for name, template in TEMPLATES.items()
        }

    def list_templates(self) -> List[PromptTemplate]:
        """List all available prompt templates."""
        return list(self.templates.values())

    def get_template(self, template_name: str) -> PromptTemplate:
        """Get a specific template by name."""
        if template_name not in self.templates:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_name}' not found"
            )
        return self.templates[template_name]

    def generate_prompt(self, request: PromptRequest) -> PromptResponse:
        """Generate a prompt using a template and variables."""
        template = self.get_template(request.template_name)
        
        # Validate that all required variables are provided
        missing_vars = set(template.variables) - set(request.variables.keys())
        if missing_vars:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required variables: {', '.join(missing_vars)}"
            )
        
        # Generate the prompt
        try:
            prompt = template.template.format(**request.variables)
        except KeyError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid variable: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating prompt: {str(e)}"
            )
        
        return PromptResponse(
            prompt=prompt,
            template_name=template.name,
            metadata=template.metadata
        ) 
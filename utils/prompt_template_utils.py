import os
import json
from typing import Dict, Any, List, Optional
import re
from string import Template
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PromptTemplate:
    """
    A class for managing prompt templates with variable substitution
    """
    
    def __init__(self, template_text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize with template text and optional metadata
        
        Args:
            template_text: String template with variables in format ${variable_name}
            metadata: Optional dictionary with template metadata
        """
        self.template_text = template_text
        self.template = Template(template_text)
        self.metadata = metadata or {}
        self.required_vars = self._extract_variables()
        
    def _extract_variables(self) -> List[str]:
        """Extract required variables from the template"""
        # Find all ${variable} patterns in the template
        pattern = r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        return re.findall(pattern, self.template_text)
    
    def render(self, **kwargs) -> str:
        """
        Render the template with the provided variables
        
        Args:
            **kwargs: Key-value pairs for template variables
            
        Returns:
            The rendered template string
        """
        # Check if all required variables are provided
        missing_vars = [var for var in self.required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        try:
            return self.template.substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {str(e)}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization"""
        return {
            "template_text": self.template_text,
            "metadata": self.metadata,
            "required_vars": self.required_vars
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create template from dictionary"""
        return cls(
            template_text=data["template_text"],
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_file(cls, filepath: str) -> 'PromptTemplate':
        """Load template from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if the file is JSON (for templates with metadata)
            if filepath.endswith('.json'):
                data = json.loads(content)
                return cls(
                    template_text=data["template_text"],
                    metadata=data.get("metadata", {})
                )
            # Otherwise treat as raw template text
            return cls(template_text=content)
        except Exception as e:
            logger.error(f"Error loading template from {filepath}: {str(e)}")
            raise


def load_prompt_templates(directory: str) -> Dict[str, PromptTemplate]:
    """
    Load all prompt templates from a directory
    
    Args:
        directory: Path to directory containing template files
        
    Returns:
        Dictionary mapping template names to PromptTemplate objects
    """
    templates = {}
    
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath) and (filepath.endswith('.txt') or filepath.endswith('.json')):
                template_name = os.path.splitext(filename)[0]
                templates[template_name] = PromptTemplate.from_file(filepath)
                logger.info(f"Loaded template: {template_name}")
    except Exception as e:
        logger.error(f"Error loading templates from {directory}: {str(e)}")
        
    return templates


def combine_templates(templates: List[PromptTemplate], separator: str = "\n\n") -> PromptTemplate:
    """
    Combine multiple templates into a single template
    
    Args:
        templates: List of PromptTemplate objects to combine
        separator: String to use between templates
        
    Returns:
        A new PromptTemplate with combined content
    """
    combined_text = separator.join(t.template_text for t in templates)
    
    # Merge metadata
    combined_metadata = {}
    for template in templates:
        if template.metadata:
            for key, value in template.metadata.items():
                if key in combined_metadata and isinstance(combined_metadata[key], list):
                    if isinstance(value, list):
                        combined_metadata[key].extend(value)
                    else:
                        combined_metadata[key].append(value)
                elif key in combined_metadata and key in template.metadata:
                    combined_metadata[key] = [combined_metadata[key], template.metadata[key]]
                else:
                    combined_metadata[key] = value
    
    return PromptTemplate(combined_text, combined_metadata) 
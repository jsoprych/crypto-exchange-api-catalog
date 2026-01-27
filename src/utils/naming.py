# src/utils/naming.py
"""
Naming convention utilities for Python/Go compatibility.
"""

import re
from typing import Any, Dict, List, Union


def to_snake_case(text: str) -> str:
    """
    Convert text to snake_case.

    Args:
        text: Input text in any case format

    Returns:
        Text in snake_case format
    """
    # Handle camelCase and PascalCase
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)

    # Convert to lowercase and replace spaces/hyphens with underscores
    text = text.lower()
    text = re.sub(r'[\s\-]+', '_', text)

    # Remove duplicate underscores
    text = re.sub(r'_+', '_', text)

    return text.strip('_')


def to_camel_case(text: str) -> str:
    """
    Convert text to camelCase.

    Args:
        text: Input text in any case format

    Returns:
        Text in camelCase format
    """
    # First convert to snake_case to normalize
    snake = to_snake_case(text)

    # Split by underscore and capitalize all but first word
    components = snake.split('_')

    if not components:
        return text

    # First component stays lowercase, rest are capitalized
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def convert_dict_keys(
    data: Union[Dict, List],
    convention: str
) -> Union[Dict, List]:
    """
    Recursively convert dictionary keys to specified naming convention.

    Args:
        data: Dictionary or list to convert
        convention: Target convention ('snake_case' or 'camelCase')

    Returns:
        Data with converted keys

    Raises:
        ValueError: If convention is not recognized
    """
    if convention not in ('snake_case', 'camelCase'):
        raise ValueError(f"Unknown convention: {convention}")

    converter = to_snake_case if convention == 'snake_case' else to_camel_case

    if isinstance(data, dict):
        return {
            converter(key): convert_dict_keys(value, convention)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_dict_keys(item, convention) for item in data]
    else:
        return data


def get_field_name(field: str, convention: str) -> str:
    """
    Convert a single field name to the specified convention.

    Args:
        field: Field name to convert
        convention: Target convention ('snake_case' or 'camelCase')

    Returns:
        Converted field name
    """
    if convention == 'snake_case':
        return to_snake_case(field)
    elif convention == 'camelCase':
        return to_camel_case(field)
    else:
        raise ValueError(f"Unknown convention: {convention}")

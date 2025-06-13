"""
Base generator class for all code generators.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import TeamMember, TeamSpecification
from ..ui.console import console, print_error, print_success


class BaseGenerator(ABC):
    """Base class for all generators."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize generator.

        Args:
            output_dir: Base output directory for generated files
        """
        self.output_dir = output_dir or Path.cwd()

    def ensure_directory(self, path: Path) -> Path:
        """
        Ensure a directory exists.

        Args:
            path: Directory path

        Returns:
            The path
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_file(self, path: Path, content: str, overwrite: bool = True) -> bool:
        """
        Write content to file.

        Args:
            path: File path
            content: File content
            overwrite: Whether to overwrite existing files

        Returns:
            True if successful
        """
        try:
            if path.exists() and not overwrite:
                print_error(f"File already exists: {path}")
                return False

            # Ensure parent directory exists
            self.ensure_directory(path.parent)

            # Write file
            path.write_text(content)
            print_success(f"Created: {path}")
            return True

        except Exception as e:
            print_error(f"Failed to write {path}: {e}")
            return False

    @abstractmethod
    def generate(self, team_spec: TeamSpecification) -> Dict[str, Any]:
        """
        Generate files for the team.

        Args:
            team_spec: Team specification

        Returns:
            Dictionary with generation results
        """
        pass

    def get_team_directory(self, team_spec: TeamSpecification) -> Path:
        """Get the team's output directory."""
        return self.output_dir / team_spec.directory_name

    def get_safe_filename(self, name: str, extension: str = ".py") -> str:
        """Convert name to safe filename."""
        # Convert to lowercase and replace spaces/hyphens with underscores
        safe_name = name.lower().replace(" ", "_").replace("-", "_")

        # Remove special characters
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

        # Ensure valid Python identifier for .py files
        if extension == ".py" and safe_name and safe_name[0].isdigit():
            safe_name = f"m_{safe_name}"

        return safe_name + extension

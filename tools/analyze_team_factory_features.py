#!/usr/bin/env python3
"""
Analyze team_factory.py to extract all features without importing it.
This ensures we capture everything before refactoring.
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TeamFactoryAnalyzer:
    """Analyzes team_factory.py to extract all features."""

    def __init__(self, file_path: str = "team_factory.py"):
        self.file_path = Path(file_path)
        self.content = self.file_path.read_text()
        self.lines = self.content.splitlines()

    def analyze(self) -> Dict:
        """Perform complete analysis."""
        return {
            "statistics": self.get_statistics(),
            "functions": self.extract_functions(),
            "classes": self.extract_classes(),
            "constants": self.extract_constants(),
            "imports": self.extract_imports(),
            "generated_files": self.extract_generated_files(),
            "template_blocks": self.extract_template_blocks(),
            "integrations": self.extract_integrations(),
            "ui_components": self.extract_ui_components(),
            "validation_patterns": self.extract_validation_patterns(),
            "llm_configurations": self.extract_llm_configs(),
            "personality_traits": self.extract_personality_traits(),
            "department_mappings": self.extract_department_mappings(),
        }

    def get_statistics(self) -> Dict:
        """Get basic file statistics."""
        return {
            "total_lines": len(self.lines),
            "total_characters": len(self.content),
            "blank_lines": sum(1 for line in self.lines if not line.strip()),
            "comment_lines": sum(
                1 for line in self.lines if line.strip().startswith("#")
            ),
            "function_count": len(
                re.findall(r"^def\s+\w+", self.content, re.MULTILINE)
            ),
            "class_count": len(re.findall(r"^class\s+\w+", self.content, re.MULTILINE)),
        }

    def extract_functions(self) -> List[Dict]:
        """Extract all function definitions with their line numbers."""
        functions = []
        pattern = re.compile(r"^def\s+(\w+)\s*\((.*?)\):", re.MULTILINE)

        for match in pattern.finditer(self.content):
            func_name = match.group(1)
            params = match.group(2)
            line_num = self.content[: match.start()].count("\n") + 1

            # Find docstring
            docstring = self._find_docstring(line_num)

            functions.append(
                {
                    "name": func_name,
                    "line": line_num,
                    "params": params,
                    "docstring": docstring,
                    "is_async": self._is_async_function(line_num),
                }
            )

        return functions

    def extract_classes(self) -> List[Dict]:
        """Extract all class definitions."""
        classes = []
        pattern = re.compile(r"^class\s+(\w+)(?:\((.*?)\))?:", re.MULTILINE)

        for match in pattern.finditer(self.content):
            class_name = match.group(1)
            base_classes = match.group(2) or ""
            line_num = self.content[: match.start()].count("\n") + 1

            # Find methods
            methods = self._find_class_methods(class_name, line_num)

            classes.append(
                {
                    "name": class_name,
                    "line": line_num,
                    "base_classes": base_classes,
                    "methods": methods,
                    "is_dataclass": "@dataclass" in self.lines[line_num - 2]
                    if line_num > 1
                    else False,
                }
            )

        return classes

    def extract_constants(self) -> List[Dict]:
        """Extract constants and global variables."""
        constants = []

        # Look for uppercase variables
        pattern = re.compile(r"^([A-Z_]+)\s*=\s*(.+)$", re.MULTILINE)
        for match in pattern.finditer(self.content):
            const_name = match.group(1)
            value = match.group(2).strip()
            line_num = self.content[: match.start()].count("\n") + 1

            constants.append(
                {
                    "name": const_name,
                    "line": line_num,
                    "value_preview": value[:100] + "..." if len(value) > 100 else value,
                }
            )

        return constants

    def extract_imports(self) -> List[str]:
        """Extract all import statements."""
        imports = []

        # Standard imports
        pattern1 = re.compile(r"^import\s+(.+)$", re.MULTILINE)
        for match in pattern1.finditer(self.content):
            imports.append(f"import {match.group(1)}")

        # From imports
        pattern2 = re.compile(r"^from\s+(\S+)\s+import\s+(.+)$", re.MULTILINE)
        for match in pattern2.finditer(self.content):
            imports.append(f"from {match.group(1)} import {match.group(2)}")

        return sorted(list(set(imports)))

    def extract_generated_files(self) -> List[str]:
        """Extract all file paths that are generated."""
        files = set()

        # Look for file creation patterns
        patterns = [
            r'open\s*\(\s*["\']([^"\']+)["\']',  # open("filename")
            r'Path\s*\(\s*["\']([^"\']+)["\']',  # Path("filename")
            r'with\s+open\s*\(\s*["\']([^"\']+)["\']',  # with open("filename")
            r"\.write_text\s*\(",  # path.write_text()
            r"mkdir\s*\(",  # directory creation
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, self.content):
                if len(match.groups()) > 0:
                    file_path = match.group(1)
                    if "/" in file_path or "." in file_path:
                        files.add(file_path)

        # Also look for f-strings with file paths
        fstring_pattern = r'f["\']([^"\']*\{[^}]+\}[^"\']*)["\']'
        for match in re.finditer(fstring_pattern, self.content):
            template = match.group(1)
            # Common file patterns
            if any(
                ext in template
                for ext in [".py", ".yaml", ".yml", ".txt", ".md", ".sh"]
            ):
                files.add(template)

        return sorted(list(files))

    def extract_template_blocks(self) -> List[Dict]:
        """Extract large template strings."""
        templates = []

        # Look for triple-quoted strings
        pattern = re.compile(
            r'(\w+)\s*=\s*(?:f?)("""|\'\'\')(.*?)\2', re.MULTILINE | re.DOTALL
        )

        for match in pattern.finditer(self.content):
            var_name = match.group(1)
            content = match.group(3)
            line_num = self.content[: match.start()].count("\n") + 1

            if len(content) > 100:  # Only large templates
                templates.append(
                    {
                        "variable": var_name,
                        "line": line_num,
                        "size": len(content),
                        "is_fstring": 'f"""'
                        in self.content[match.start() : match.end()],
                        "preview": content[:200] + "..."
                        if len(content) > 200
                        else content,
                    }
                )

        return templates

    def extract_integrations(self) -> List[str]:
        """Extract external integrations mentioned."""
        integrations = set()

        # Look for common integration patterns
        patterns = {
            "supabase": r"supabase|team_registry",
            "qdrant": r"qdrant|vector|memory",
            "a2a": r"a2a|A2AClient|agent.to.agent",
            "mcp": r"mcp|agentgateway",
            "prometheus": r"prometheus|metrics",
            "llm_providers": r"OpenAI|Anthropic|claude|gpt",
            "docker": r"Docker|dockerfile|container",
            "kubernetes": r"k8s|kubernetes|deployment\.yaml",
            "logging": r"logging|logger|conversation_log",
            "monitoring": r"monitoring|cost_track|quota",
        }

        for name, pattern in patterns.items():
            if re.search(pattern, self.content, re.IGNORECASE):
                integrations.add(name)

        return sorted(list(integrations))

    def extract_ui_components(self) -> List[str]:
        """Extract UI/Rich console components used."""
        ui_components = set()

        # Look for Rich imports and usage
        rich_patterns = [
            r"from rich import (.+)",
            r"from rich\.\w+ import (.+)",
            r"Console\(",
            r"Panel\(",
            r"Table\(",
            r"Progress\(",
            r"Prompt\.ask",
            r"Confirm\.ask",
            r"console\.\w+",
        ]

        for pattern in rich_patterns:
            for match in re.finditer(pattern, self.content):
                if match.groups():
                    components = match.group(1).split(",")
                    ui_components.update(c.strip() for c in components)
                else:
                    ui_components.add(pattern.replace("\\", "").replace("(", ""))

        return sorted(list(ui_components))

    def extract_validation_patterns(self) -> List[str]:
        """Extract validation rules."""
        validations = set()

        # Look for validation patterns
        patterns = {
            "team_size": r"len\(.*members.*\)\s*[<>]=?\s*\d+",
            "name_validation": r"sanitize.*name|name.*validation",
            "directory_check": r"exists\(\)|is_dir\(\)",
            "member_validation": r"unique.*member|duplicate.*check",
            "department_validation": r"department.*in\s*\[",
            "framework_check": r'framework\s*==\s*["\']',
            "manager_check": r"is_manager|has_manager",
            "skeptic_rule": r"skeptic.*team.*>=?\s*5",
        }

        for name, pattern in patterns.items():
            if re.search(pattern, self.content, re.IGNORECASE):
                validations.add(name)

        return sorted(list(validations))

    def extract_llm_configs(self) -> Dict:
        """Extract LLM configurations."""
        configs = {
            "providers": set(),
            "models": set(),
            "fallback_mentioned": False,
        }

        # Providers
        if "OpenAI" in self.content:
            configs["providers"].add("OpenAI")
        if "Anthropic" in self.content:
            configs["providers"].add("Anthropic")

        # Models
        model_patterns = [
            r'gpt-4[^\s"\']*',
            r'gpt-3\.5[^\s"\']*',
            r'claude-3[^\s"\']*',
            r'claude-2[^\s"\']*',
        ]

        for pattern in model_patterns:
            for match in re.finditer(pattern, self.content):
                configs["models"].add(match.group(0))

        # Fallback
        if "fallback" in self.content.lower() and "llm" in self.content.lower():
            configs["fallback_mentioned"] = True

        configs["providers"] = sorted(list(configs["providers"]))
        configs["models"] = sorted(list(configs["models"]))

        return configs

    def extract_personality_traits(self) -> List[str]:
        """Extract personality traits."""
        traits = set()

        # Look for personality definitions
        pattern = r'["\'](?:skeptic|optimist|detail-oriented|innovator|pragmatist|collaborator|analyzer)["\']'

        for match in re.finditer(pattern, self.content):
            trait = match.group(0).strip("\"'")
            traits.add(trait)

        return sorted(list(traits))

    def extract_department_mappings(self) -> Dict:
        """Extract department to executive mappings."""
        mappings = {}

        # Look for department mapping patterns
        exec_pattern = r"(?:cto|cmo|coo|cfo|ceo).*\[(.*?)\]"

        for match in re.finditer(exec_pattern, self.content, re.IGNORECASE | re.DOTALL):
            departments = match.group(1)
            # Extract department names
            dept_matches = re.findall(r'["\'](\w+)["\']', departments)

            exec_name = re.search(
                r"(cto|cmo|coo|cfo|ceo)", match.group(0), re.IGNORECASE
            )
            if exec_name and dept_matches:
                mappings[exec_name.group(1).lower()] = dept_matches

        return mappings

    def _find_docstring(self, line_num: int) -> str:
        """Find docstring for a function."""
        if line_num < len(self.lines):
            # Check next few lines for docstring
            for i in range(line_num, min(line_num + 5, len(self.lines))):
                line = self.lines[i].strip()
                if line.startswith('"""') or line.startswith("'''"):
                    # Extract docstring
                    quote = '"""' if line.startswith('"""') else "'''"
                    if line.endswith(quote) and len(line) > 6:
                        return line[3:-3]
                    # Multi-line docstring
                    for j in range(i + 1, len(self.lines)):
                        if quote in self.lines[j]:
                            return "Multi-line docstring"
        return ""

    def _is_async_function(self, line_num: int) -> bool:
        """Check if function is async."""
        if line_num > 0:
            return "async def" in self.lines[line_num - 1]
        return False

    def _find_class_methods(self, class_name: str, start_line: int) -> List[str]:
        """Find methods in a class."""
        methods = []
        indent_level = None

        for i in range(start_line, len(self.lines)):
            line = self.lines[i]

            # Determine class indent level
            if indent_level is None and line.strip():
                indent_level = len(line) - len(line.lstrip())

            # Check if we're still in the class
            if (
                indent_level is not None
                and line.strip()
                and len(line) - len(line.lstrip()) <= indent_level
            ):
                if not line.lstrip().startswith("def"):
                    break

            # Look for method definitions
            if "def " in line and indent_level is not None:
                match = re.search(r"def\s+(\w+)\s*\(", line)
                if match:
                    methods.append(match.group(1))

        return methods

    def create_feature_summary(self) -> str:
        """Create a human-readable summary."""
        analysis = self.analyze()

        summary = f"""# Team Factory Feature Analysis

## File Statistics
- Total Lines: {analysis['statistics']['total_lines']:,}
- Functions: {analysis['statistics']['function_count']}
- Classes: {analysis['statistics']['class_count']}

## Core Components

### Classes ({len(analysis['classes'])})
{chr(10).join(f"- {c['name']} (line {c['line']})" for c in analysis['classes'])}

### Key Functions ({len(analysis['functions'])})
{chr(10).join(f"- {f['name']}() (line {f['line']})" for f in analysis['functions'][:20])}
{"... and " + str(len(analysis['functions']) - 20) + " more" if len(analysis['functions']) > 20 else ""}

### Generated Files ({len(analysis['generated_files'])})
{chr(10).join(f"- {f}" for f in analysis['generated_files'][:15])}
{"... and " + str(len(analysis['generated_files']) - 15) + " more" if len(analysis['generated_files']) > 15 else ""}

### Integrations ({len(analysis['integrations'])})
{chr(10).join(f"- {i}" for i in analysis['integrations'])}

### UI Components ({len(analysis['ui_components'])})
{chr(10).join(f"- {c}" for c in analysis['ui_components'])}

### Personality Traits ({len(analysis['personality_traits'])})
{chr(10).join(f"- {t}" for t in analysis['personality_traits'])}

### LLM Configuration
- Providers: {', '.join(analysis['llm_configurations']['providers'])}
- Models: {', '.join(analysis['llm_configurations']['models'])}
- Fallback System: {'Yes' if analysis['llm_configurations']['fallback_mentioned'] else 'No'}

### Department Mappings
{chr(10).join(f"- {exec}: {', '.join(depts)}" for exec, depts in analysis['department_mappings'].items())}

### Validation Rules ({len(analysis['validation_patterns'])})
{chr(10).join(f"- {v}" for v in analysis['validation_patterns'])}

### Template Blocks ({len(analysis['template_blocks'])})
{chr(10).join(f"- {t['variable']} ({t['size']:,} chars, line {t['line']})" for t in analysis['template_blocks'][:10])}
{"... and " + str(len(analysis['template_blocks']) - 10) + " more" if len(analysis['template_blocks']) > 10 else ""}

## Refactoring Considerations

1. **Large Templates**: {sum(1 for t in analysis['template_blocks'] if t['size'] > 500)} templates over 500 characters
2. **Complex Functions**: Identify functions that need breaking down
3. **External Dependencies**: {len(analysis['imports'])} imports to manage
4. **File Generation Logic**: Extensive file creation patterns to preserve
"""
        return summary


def main():
    """Run the analysis."""
    analyzer = TeamFactoryAnalyzer()

    # Perform analysis
    print("Analyzing team_factory.py...")
    analysis = analyzer.analyze()

    # Save detailed analysis
    with open("team_factory_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Create summary
    summary = analyzer.create_feature_summary()
    with open("team_factory_analysis_summary.md", "w") as f:
        f.write(summary)

    print("✓ Analysis complete")
    print(f"✓ Found {analysis['statistics']['function_count']} functions")
    print(f"✓ Found {analysis['statistics']['class_count']} classes")
    print(f"✓ Found {len(analysis['generated_files'])} generated file patterns")
    print(f"✓ Found {len(analysis['integrations'])} integrations")
    print("\nFiles created:")
    print("- team_factory_analysis.json (detailed analysis)")
    print("- team_factory_analysis_summary.md (human-readable summary)")


if __name__ == "__main__":
    main()

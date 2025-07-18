"""
Analysis Playbooks Package.

This package contains specialized analysis playbooks that target specific
architectural issues, anti-patterns, and security vulnerabilities.
"""

from .base_playbook import BasePlaybook
from .god_classes import GodClassesPlaybook
from .circular_dependencies import CircularDependenciesPlaybook
from .high_complexity import HighComplexityPlaybook
from .dependency_health import DependencyHealthPlaybook
from .hardcoded_secrets import HardcodedSecretsPlaybook
from .idor_vulnerabilities import IdorVulnerabilitiesPlaybook

__all__ = [
    "BasePlaybook",
    "GodClassesPlaybook",
    "CircularDependenciesPlaybook",
    "HighComplexityPlaybook",
    "DependencyHealthPlaybook",
    "HardcodedSecretsPlaybook",
    "IdorVulnerabilitiesPlaybook"
] 
"""
Hardcoded Secrets Detection Playbook.

Specialized playbook for detecting hardcoded secrets, credentials,
API keys, and other sensitive information in the codebase.
"""

import re
from typing import Dict, List, Any
from .base_playbook import BasePlaybook
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class HardcodedSecretsPlaybook(BasePlaybook):
    """
    Playbook for detecting hardcoded secrets and credentials.
    
    Detects:
    - API keys and tokens
    - Database credentials
    - Encryption keys
    - Service passwords
    - SSH keys and certificates
    """
    
    def __init__(self):
        super().__init__(
            name="hardcoded_secrets",
            description="Detects hardcoded secrets, credentials, and sensitive information",
            version="1.0.0"
        )
        
        # Comprehensive secret patterns
        self.secret_patterns = {
            "api_key": [
                r"api[_-]?key['\"\s]*[:=]['\"\s]*[a-zA-Z0-9_-]{20,}",
                r"apikey['\"\s]*[:=]['\"\s]*[a-zA-Z0-9_-]{20,}",
                r"key['\"\s]*[:=]['\"\s]*[a-zA-Z0-9_-]{32,}"
            ],
            "password": [
                r"password['\"\s]*[:=]['\"\s]*['\"][^'\"]{8,}['\"]",
                r"passwd['\"\s]*[:=]['\"\s]*['\"][^'\"]{8,}['\"]",
                r"pwd['\"\s]*[:=]['\"\s]*['\"][^'\"]{8,}['\"]"
            ],
            "token": [
                r"token['\"\s]*[:=]['\"\s]*['\"][a-zA-Z0-9_-]{20,}['\"]",
                r"access[_-]?token['\"\s]*[:=]['\"\s]*['\"][a-zA-Z0-9_-]{20,}['\"]",
                r"bearer[_-]?token['\"\s]*[:=]['\"\s]*['\"][a-zA-Z0-9_-]{20,}['\"]"
            ],
            "database_credential": [
                r"(mysql|postgresql|mongodb)://[^'\"\s]+",
                r"database[_-]?url['\"\s]*[:=]['\"\s]*['\"][^'\"]+['\"]",
                r"db[_-]?(user|password)['\"\s]*[:=]['\"\s]*['\"][^'\"]+['\"]"
            ],
            "private_key": [
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                r"private[_-]?key['\"\s]*[:=]['\"\s]*['\"][^'\"]{40,}['\"]"
            ],
            "aws_credential": [
                r"AKIA[0-9A-Z]{16}",
                r"aws[_-]?access[_-]?key['\"\s]*[:=]['\"\s]*['\"][^'\"]+['\"]",
                r"aws[_-]?secret['\"\s]*[:=]['\"\s]*['\"][^'\"]+['\"]"
            ],
            "jwt_token": [
                r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
                r"jwt[_-]?token['\"\s]*[:=]['\"\s]*['\"]eyJ[^'\"]+['\"]"
            ]
        }
    
    async def execute(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Execute hardcoded secrets detection analysis."""
        self.logger.info(f"Starting hardcoded secrets analysis for task {context.task_id}")
        
        try:
            search_queries = [
                "api key token password credential",
                "secret environment variable configuration",
                "database connection string url",
                "authentication authorization bearer",
                "private key certificate encryption"
            ]
            
            code_results = await self._search_patterns(context, search_queries, max_results=25)
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Hardcoded Secrets Analysis Complete - No Secrets Found",
                    description="No hardcoded secrets detected in the codebase.",
                    confidence_score=0.8
                )
            
            secret_findings = []
            
            for result in code_results:
                # Skip test files and documentation
                if self._should_skip_file(result["file_path"]):
                    continue
                    
                findings = await self._scan_for_secrets(result)
                secret_findings.extend(findings)
            
            # Remove duplicates and false positives
            secret_findings = self._filter_findings(secret_findings)
            
            overall_severity = self._assess_secrets_severity(secret_findings)
            recommendations = self._generate_targeted_recommendations("hardcoded_secrets", secret_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Hardcoded Secrets Analysis Complete - {len(secret_findings)} Secrets Found",
                description=f"Detected {len(secret_findings)} potential hardcoded secrets that require immediate attention.",
                findings=secret_findings,
                recommendations=recommendations,
                confidence_score=0.95,
                metadata={
                    "playbook_version": self.version,
                    "files_scanned": len(code_results),
                    "secrets_by_type": self._categorize_secrets(secret_findings),
                    "critical_secrets": len([f for f in secret_findings if f.get("severity") == "critical"])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Hardcoded secrets analysis failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Hardcoded Secrets Analysis Failed",
                description=f"Analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped from secret scanning."""
        skip_patterns = [
            "test", "spec", "mock", "example", "demo", "sample",
            "readme", "doc", "documentation", ".md", ".txt",
            "node_modules", "__pycache__", ".git"
        ]
        return any(pattern in file_path.lower() for pattern in skip_patterns)
    
    async def _scan_for_secrets(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan content for hardcoded secrets."""
        findings = []
        content = result["content"]
        file_path = result["file_path"]
        lines = content.split('\n')
        
        for secret_type, patterns in self.secret_patterns.items():
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        matched_text = match.group(0)
                        
                        # Additional validation to reduce false positives
                        if self._is_likely_secret(matched_text, secret_type):
                            masked_text = self._mask_secret(matched_text)
                            
                            findings.append({
                                "type": "hardcoded_secret",
                                "pattern": secret_type,
                                "severity": self._get_secret_severity(secret_type),
                                "file": file_path,
                                "line": line_num,
                                "message": f"Hardcoded {secret_type.replace('_', ' ')} detected",
                                "content_preview": masked_text,
                                "metadata": {
                                    "secret_type": secret_type,
                                    "confidence": self._calculate_confidence(matched_text, secret_type),
                                    "line_content": lines[line_num - 1].strip()[:100] if line_num <= len(lines) else ""
                                }
                            })
                except re.error:
                    continue
        
        return findings
    
    def _is_likely_secret(self, text: str, secret_type: str) -> bool:
        """Additional validation to reduce false positives."""
        # Skip obvious false positives
        false_positive_patterns = [
            "example", "dummy", "test", "fake", "placeholder",
            "your_", "my_", "insert_", "add_your", "replace_with",
            "xxx", "000", "123", "abc", "password123"
        ]
        
        text_lower = text.lower()
        if any(fp in text_lower for fp in false_positive_patterns):
            return False
        
        # Type-specific validation
        if secret_type == "password":
            # Passwords should have reasonable complexity
            if len(text) < 8 or text.isdigit() or text.isalpha():
                return False
        
        elif secret_type == "api_key":
            # API keys should be sufficiently random
            if text.count('a') > len(text) * 0.3:  # Too many 'a's
                return False
        
        return True
    
    def _mask_secret(self, text: str) -> str:
        """Mask sensitive parts of detected secrets."""
        if len(text) <= 8:
            return "*" * len(text)
        
        # Show first 3 and last 3 characters, mask the middle
        return text[:3] + "*" * (len(text) - 6) + text[-3:]
    
    def _get_secret_severity(self, secret_type: str) -> str:
        """Get severity level for different secret types."""
        critical_secrets = ["private_key", "database_credential", "aws_credential"]
        high_secrets = ["password", "api_key", "jwt_token"]
        
        if secret_type in critical_secrets:
            return "critical"
        elif secret_type in high_secrets:
            return "high"
        else:
            return "medium"
    
    def _calculate_confidence(self, text: str, secret_type: str) -> float:
        """Calculate confidence score for secret detection."""
        base_confidence = 0.8
        
        # Increase confidence for longer strings
        if len(text) > 32:
            base_confidence += 0.1
        
        # Increase confidence for mixed case and special characters
        if any(c.isupper() for c in text) and any(c.islower() for c in text):
            base_confidence += 0.05
        
        if any(c in text for c in "!@#$%^&*()_+-=[]{}|;:,.<>?"):
            base_confidence += 0.05
        
        return min(0.99, base_confidence)
    
    def _filter_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicates and false positives."""
        filtered = []
        seen = set()
        
        for finding in findings:
            # Create unique key based on file, line, and pattern
            key = (finding["file"], finding["line"], finding["pattern"])
            
            if key not in seen:
                seen.add(key)
                filtered.append(finding)
        
        return filtered
    
    def _categorize_secrets(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize secrets by type."""
        categories = {}
        for finding in findings:
            secret_type = finding.get("pattern", "unknown")
            categories[secret_type] = categories.get(secret_type, 0) + 1
        return categories
    
    def _assess_secrets_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall secrets severity."""
        if not findings:
            return SeverityLevel.LOW
        
        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        high_count = len([f for f in findings if f.get("severity") == "high"])
        
        # Any hardcoded secret is serious
        if critical_count > 0:
            return SeverityLevel.CRITICAL
        elif high_count > 0 or len(findings) > 2:
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.MEDIUM 
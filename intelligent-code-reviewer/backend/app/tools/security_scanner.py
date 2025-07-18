"""
Security Scanner Tool.

Performs comprehensive security analysis to detect vulnerabilities,
hardcoded secrets, unsafe patterns, and potential security risks.
"""

import re
from typing import Dict, List, Any
from .base_tool import BaseTool
from ..services.ai_agent import AnalysisResult, AnalysisStatus, SeverityLevel, AgentContext


class SecurityScanner(BaseTool):
    """
    Security analysis tool for vulnerability and risk assessment.
    
    Scans for:
    - Hardcoded secrets and credentials
    - SQL injection vulnerabilities
    - XSS vulnerabilities  
    - Authentication and authorization issues
    - Insecure data handling
    - Unsafe cryptographic practices
    """
    
    def __init__(self):
        super().__init__(
            name="security_scanner",
            description="Comprehensive security vulnerability scanning and risk assessment",
            version="1.0.0"
        )
        
        # Security pattern definitions
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
                r"auth[_-]?token['\"\s]*[:=]['\"\s]*['\"][a-zA-Z0-9_-]{20,}['\"]"
            ],
            "database_url": [
                r"(mysql|postgresql|mongodb)://[^'\"\s]+",
                r"database[_-]?url['\"\s]*[:=]['\"\s]*['\"][^'\"]+['\"]",
                r"db[_-]?url['\"\s]*[:=]['\"\s]*['\"][^'\"]+['\"]"
            ],
            "private_key": [
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                r"private[_-]?key['\"\s]*[:=]['\"\s]*['\"][^'\"]{40,}['\"]"
            ]
        }
        
        self.vulnerability_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*['\"].*\+.*['\"]",
                r"query\s*\(\s*['\"].*\+.*['\"]",
                r"SELECT.*\+.*FROM",
                r"INSERT.*\+.*VALUES",
                r"UPDATE.*\+.*SET",
                r"DELETE.*\+.*WHERE"
            ],
            "xss": [
                r"innerHTML\s*=\s*.*\+",
                r"document\.write\s*\(",
                r"eval\s*\(\s*.*\+",
                r"setTimeout\s*\(\s*['\"].*\+",
                r"setInterval\s*\(\s*['\"].*\+"
            ],
            "command_injection": [
                r"exec\s*\(\s*.*\+",
                r"system\s*\(\s*.*\+",
                r"os\.system\s*\(\s*.*\+",
                r"subprocess\.\w+\s*\(\s*.*\+",
                r"shell_exec\s*\(\s*.*\+"
            ],
            "path_traversal": [
                r"\.\.\/",
                r"\.\.\\\\ ",
                r"\/etc\/passwd",
                r"\/windows\/system32"
            ],
            "unsafe_deserialization": [
                r"pickle\.loads\s*\(",
                r"cPickle\.loads\s*\(",
                r"eval\s*\(",
                r"exec\s*\(",
                r"__import__\s*\("
            ]
        }
    
    async def analyze(self, context: AgentContext, config: Dict[str, Any] = None) -> AnalysisResult:
        """Perform security analysis on the codebase."""
        self.logger.info(f"Starting security scan for task {context.task_id}")
        
        try:
            # Define search patterns for security analysis
            search_queries = [
                # Authentication and authorization
                "authentication login password auth token",
                "authorization permission role access control",
                "session cookie jwt oauth credential",
                
                # Data handling
                "database query sql execute statement",
                "input validation sanitize escape",
                "encryption decrypt hash crypto password",
                
                # Network and communication
                "http request response api endpoint",
                "ssl tls certificate secure connection",
                "cors origin header security policy",
                
                # File and system operations
                "file upload download path directory",
                "execute command system shell subprocess",
                "environment variable config secret",
                
                # Error handling and logging
                "exception error logging debug trace",
                "try catch finally throw raise",
                "console log print debug output"
            ]
            
            # Search for security-related code patterns
            code_results = await self._search_code_patterns(
                context, search_queries, max_results=20
            )
            
            if not code_results:
                return self._create_result(
                    status=AnalysisStatus.COMPLETED,
                    severity=SeverityLevel.LOW,
                    title="Security Scan Complete - No Issues Found",
                    description="Security analysis completed with no significant vulnerabilities detected.",
                    confidence_score=0.7
                )
            
            # Scan for hardcoded secrets
            secret_findings = await self._scan_for_secrets(code_results)
            
            # Scan for vulnerability patterns
            vulnerability_findings = await self._scan_for_vulnerabilities(code_results)
            
            # Analyze security configuration issues
            config_findings = await self._analyze_security_config(code_results)
            
            # Combine all security findings
            all_findings = secret_findings + vulnerability_findings + config_findings
            
            # Assess overall security risk
            overall_severity = self._assess_security_severity(all_findings)
            
            # Generate security recommendations
            recommendations = self._generate_security_recommendations(all_findings)
            
            return self._create_result(
                status=AnalysisStatus.COMPLETED,
                severity=overall_severity,
                title=f"Security Scan Complete - {len(all_findings)} Issues Found",
                description=f"Security analysis identified {len(all_findings)} potential security issues including {len(secret_findings)} secret exposures and {len(vulnerability_findings)} vulnerabilities.",
                findings=all_findings,
                recommendations=recommendations,
                confidence_score=0.9,
                metadata={
                    "tool_version": self.version,
                    "scan_coverage": {
                        "files_scanned": len(set(r["file_path"] for r in code_results)),
                        "secret_patterns_checked": len(self.secret_patterns),
                        "vulnerability_patterns_checked": len(self.vulnerability_patterns)
                    },
                    "finding_breakdown": {
                        "secrets": len(secret_findings),
                        "vulnerabilities": len(vulnerability_findings),
                        "configuration_issues": len(config_findings)
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            return self._create_result(
                status=AnalysisStatus.FAILED,
                severity=SeverityLevel.LOW,
                title="Security Scan Failed",
                description=f"Security analysis encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def _scan_for_secrets(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan for hardcoded secrets and credentials."""
        secret_findings = []
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            
            # Skip test files and documentation
            if any(skip in file_path.lower() for skip in ["test", "spec", "mock", "example", "readme", "doc"]):
                continue
            
            lines = content.split("\n")
            
            for secret_type, patterns in self.secret_patterns.items():
                for pattern in patterns:
                    try:
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            # Find line number
                            line_num = content[:match.start()].count('\n') + 1
                            
                            # Extract matched content (mask sensitive parts)
                            matched_text = match.group(0)
                            masked_text = self._mask_sensitive_data(matched_text)
                            
                            secret_findings.append({
                                "type": "security_secret",
                                "pattern": secret_type,
                                "severity": "critical" if secret_type in ["password", "private_key"] else "high",
                                "file": file_path,
                                "line": line_num,
                                "message": f"Hardcoded {secret_type.replace('_', ' ')} detected",
                                "content_preview": masked_text,
                                "metadata": {
                                    "secret_type": secret_type,
                                    "pattern_matched": pattern,
                                    "confidence": 0.9
                                }
                            })
                    except re.error:
                        continue
        
        return secret_findings
    
    async def _scan_for_vulnerabilities(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan for security vulnerability patterns."""
        vulnerability_findings = []
        
        for result in code_results:
            content = result["content"]
            file_path = result["file_path"]
            lines = content.split("\n")
            
            for vuln_type, patterns in self.vulnerability_patterns.items():
                for pattern in patterns:
                    try:
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            matched_line = lines[line_num - 1] if line_num <= len(lines) else ""
                            
                            vulnerability_findings.append({
                                "type": "security_vulnerability",
                                "pattern": vuln_type,
                                "severity": self._get_vulnerability_severity(vuln_type),
                                "file": file_path,
                                "line": line_num,
                                "message": f"Potential {vuln_type.replace('_', ' ')} vulnerability",
                                "content_preview": matched_line.strip()[:100],
                                "metadata": {
                                    "vulnerability_type": vuln_type,
                                    "pattern_matched": pattern,
                                    "confidence": 0.8
                                }
                            })
                    except re.error:
                        continue
        
        return vulnerability_findings
    
    async def _analyze_security_config(self, code_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze security configuration issues."""
        config_findings = []
        
        # Security configuration patterns
        insecure_patterns = [
            ("debug = true", "high", "Debug mode enabled in production"),
            ("ssl = false", "high", "SSL/TLS disabled"),
            ("verify = false", "medium", "Certificate verification disabled"),
            ("allow_redirects = true", "medium", "Automatic redirects allowed"),
            ("safe_mode = false", "medium", "Safe mode disabled"),
            (".strip_tags(", "low", "HTML tag stripping - ensure proper escaping"),
            ("cors_allow_all", "medium", "CORS allows all origins"),
            ("x-frame-options: allow", "medium", "Frame options allow clickjacking")
        ]
        
        for result in code_results:
            content_lower = result["content"].lower()
            file_path = result["file_path"]
            
            for pattern, severity, message in insecure_patterns:
                if pattern.lower() in content_lower:
                    # Find line number
                    lines = result["content"].split("\n")
                    line_num = None
                    for i, line in enumerate(lines):
                        if pattern.lower() in line.lower():
                            line_num = i + 1
                            break
                    
                    config_findings.append({
                        "type": "security_configuration",
                        "pattern": pattern.replace(" ", "_"),
                        "severity": severity,
                        "file": file_path,
                        "line": line_num,
                        "message": message,
                        "content_preview": lines[line_num - 1].strip()[:100] if line_num else "",
                        "metadata": {
                            "config_type": "security_setting",
                            "recommendation": "Review and secure this configuration"
                        }
                    })
        
        return config_findings
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive parts of detected secrets."""
        # Replace potential secrets with asterisks, keeping first/last few chars
        if len(text) > 10:
            return text[:3] + "*" * (len(text) - 6) + text[-3:]
        else:
            return "*" * len(text)
    
    def _get_vulnerability_severity(self, vuln_type: str) -> str:
        """Get severity level for different vulnerability types."""
        critical_vulns = ["sql_injection", "command_injection", "unsafe_deserialization"]
        high_vulns = ["xss", "path_traversal"]
        
        if vuln_type in critical_vulns:
            return "critical"
        elif vuln_type in high_vulns:
            return "high"
        else:
            return "medium"
    
    def _assess_security_severity(self, findings: List[Dict[str, Any]]) -> SeverityLevel:
        """Assess overall security severity."""
        if not findings:
            return SeverityLevel.LOW
        
        severity_counts = {}
        for finding in findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Security issues are generally more serious
        if severity_counts.get("critical", 0) > 0:
            return SeverityLevel.CRITICAL
        elif severity_counts.get("high", 0) > 0:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 3 or len(findings) > 8:
            return SeverityLevel.HIGH
        elif severity_counts.get("medium", 0) > 0 or len(findings) > 3:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_security_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security-specific recommendations."""
        if not findings:
            return [
                "✅ No significant security issues detected",
                "🛡️ Consider regular security audits and penetration testing",
                "🔒 Implement security headers and HTTPS enforcement"
            ]
        
        recommendations = []
        
        # Categorize findings
        secrets = [f for f in findings if f.get("type") == "security_secret"]
        vulnerabilities = [f for f in findings if f.get("type") == "security_vulnerability"]
        config_issues = [f for f in findings if f.get("type") == "security_configuration"]
        
        # Critical security recommendations
        if secrets:
            recommendations.append(
                f"🚨 URGENT: Remove {len(secrets)} hardcoded secrets - use environment variables or secret management"
            )
        
        if vulnerabilities:
            recommendations.append(
                f"⚠️ CRITICAL: Fix {len(vulnerabilities)} security vulnerabilities immediately"
            )
        
        if config_issues:
            recommendations.append(
                f"🔧 Review {len(config_issues)} security configuration issues"
            )
        
        # Pattern-specific recommendations
        vuln_types = set(f.get("pattern", "") for f in vulnerabilities)
        
        if "sql_injection" in vuln_types:
            recommendations.append("💉 Use parameterized queries to prevent SQL injection")
        
        if "xss" in vuln_types:
            recommendations.append("🌐 Implement proper input validation and output encoding for XSS prevention")
        
        if "command_injection" in vuln_types:
            recommendations.append("🖥️ Avoid dynamic command execution - use safe alternatives")
        
        # General security recommendations
        security_recommendations = [
            "🔐 Implement comprehensive input validation and sanitization",
            "🛡️ Set up Web Application Firewall (WAF) and security headers",
            "📋 Conduct regular security code reviews and automated scanning",
            "🔑 Implement proper authentication and authorization mechanisms",
            "📊 Set up security monitoring and incident response procedures"
        ]
        
        recommendations.extend(security_recommendations)
        
        return recommendations[:6] 
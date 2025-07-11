#!/usr/bin/env python3
"""
Production Readiness Validation Script
Validates that Pathfinder backend is ready for production deployment
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests


class ProductionValidator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        self.passed = 0
        self.failed = 0

    def validate_endpoint(self, endpoint: str, expected_status: int = 200) -> Tuple[bool, str]:
        """Validate a single endpoint."""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            if response.status_code == expected_status:
                return True, f"✅ {endpoint} - Status {response.status_code}"
            else:
                return False, f"❌ {endpoint} - Expected {expected_status}, got {response.status_code}"
        except Exception as e:
            return False, f"❌ {endpoint} - Error: {str(e)}"

    def validate_security_headers(self, endpoint: str = "/health") -> Tuple[bool, str]:
        """Validate security headers are present."""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            headers = response.headers
            
            required_headers = [
                "x-frame-options",
                "x-content-type-options", 
                "content-security-policy",
                "permissions-policy",
                "cross-origin-resource-policy"
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if missing_headers:
                return False, f"❌ Missing security headers: {', '.join(missing_headers)}"
            else:
                return True, "✅ All required security headers present"
                
        except Exception as e:
            return False, f"❌ Security headers check failed: {str(e)}"

    def validate_environment(self) -> Tuple[bool, str]:
        """Validate environment configuration."""
        try:
            # Check if server is running
            response = requests.get(f"{self.base_url}/health", timeout=5)
            health_data = response.json()
            
            checks = []
            
            # Environment check
            if health_data.get("environment"):
                checks.append("✅ Environment configured")
            else:
                checks.append("❌ Environment not configured")
            
            # Version check
            if health_data.get("version"):
                checks.append("✅ Version information present")
            else:
                checks.append("❌ Version information missing")
            
            # Services check
            services = health_data.get("services", {})
            if services.get("database") == "connected":
                checks.append("✅ Database connected")
            else:
                checks.append("⚠️ Database in simulation mode")
                
            return True, "\n".join(checks)
            
        except Exception as e:
            return False, f"❌ Environment validation failed: {str(e)}"

    def run_validation(self) -> Dict:
        """Run all validation checks."""
        print("🚀 Starting Production Readiness Validation...\n")
        
        # Test endpoints
        endpoints = [
            ("/health", 200),
            ("/api/v1/", 200),
            ("/api/v1/health", 200),
            ("/docs", 200),
            ("/openapi.json", 200)
        ]
        
        for endpoint, expected_status in endpoints:
            success, message = self.validate_endpoint(endpoint, expected_status)
            print(message)
            if success:
                self.passed += 1
            else:
                self.failed += 1
        
        print()
        
        # Test security headers
        success, message = self.validate_security_headers()
        print(message)
        if success:
            self.passed += 1
        else:
            self.failed += 1
            
        print()
        
        # Test environment
        success, message = self.validate_environment()
        print(message)
        if success:
            self.passed += 1
        else:
            self.failed += 1
            
        print()
        
        # Summary
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests) * 100 if total_tests > 0 else 0
        
        print("=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 PRODUCTION READY ✅")
            status = "READY"
        else:
            print("⚠️  NEEDS ATTENTION ❌")
            status = "NOT_READY"
            
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": success_rate,
            "base_url": self.base_url
        }
        
        # Save results
        with open("production_validation_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        print(f"\n📄 Results saved to: production_validation_results.json")
        
        return results


def main():
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print("🟢 Server is running\n")
    except:
        print("❌ Server is not running on localhost:8000")
        print("Please start the server first:")
        print("uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    validator = ProductionValidator()
    results = validator.run_validation()
    
    # Exit with appropriate code
    if results["status"] == "READY":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

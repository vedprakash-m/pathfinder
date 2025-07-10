#!/usr/bin/env python3
"""
Production Deployment Validation Script
Validates the Pathfinder production deployment
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

class ProductionValidator:
    def __init__(self):
        self.resource_group = "pathfinder-rg"
        self.results = {
            "validation_time": datetime.now().isoformat(),
            "deployment_status": "unknown",
            "resources": {},
            "endpoints": {},
            "tests_passed": 0,
            "tests_failed": 0,
            "recommendations": []
        }

    def run_command(self, command: str) -> Dict[str, Any]:
        """Run a shell command and return the result"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    async def validate_azure_resources(self) -> bool:
        """Validate Azure resources are deployed correctly"""
        print("🔍 Validating Azure resources...")
        
        # Check resource group exists
        cmd = f"az group exists --name {self.resource_group}"
        result = self.run_command(cmd)
        
        if not result["success"] or result["stdout"] != "true":
            print(f"  ❌ Resource group {self.resource_group} not found")
            self.results["tests_failed"] += 1
            return False
        
        print(f"  ✅ Resource group {self.resource_group} exists")
        
        # List resources
        cmd = f"az resource list --resource-group {self.resource_group} --query '[].{{name:name,type:type,provisioningState:properties.provisioningState}}'"
        result = self.run_command(cmd)
        
        if result["success"]:
            try:
                resources = json.loads(result["stdout"])
                self.results["resources"] = resources
                
                # Check critical resources
                required_resources = [
                    "Microsoft.App/containerApps",  # Backend and Frontend
                    "Microsoft.DocumentDB/databaseAccounts",  # Cosmos DB
                    "Microsoft.Sql/servers",  # SQL Server
                    "Microsoft.KeyVault/vaults",  # Key Vault
                    "Microsoft.ContainerRegistry/registries",  # Container Registry
                ]
                
                deployed_types = {r["type"] for r in resources}
                missing_resources = []
                
                for required in required_resources:
                    if required not in deployed_types:
                        missing_resources.append(required)
                
                if missing_resources:
                    print("  ❌ Missing required resources:")
                    for missing in missing_resources:
                        print(f"    - {missing}")
                    self.results["tests_failed"] += 1
                    return False
                else:
                    print(f"  ✅ All {len(resources)} resources deployed successfully")
                    self.results["tests_passed"] += 1
                    return True
                    
            except json.JSONDecodeError:
                print("  ❌ Failed to parse resource list")
                self.results["tests_failed"] += 1
                return False
        else:
            print(f"  ❌ Failed to list resources: {result['stderr']}")
            self.results["tests_failed"] += 1
            return False

    async def validate_container_apps(self) -> bool:
        """Validate Container Apps are deployed and accessible"""
        print("🚀 Validating Container Apps...")
        
        apps = ["pathfinder-backend", "pathfinder-frontend"]
        app_urls = {}
        
        for app in apps:
            cmd = f"az containerapp show --name {app} --resource-group {self.resource_group} --query '{{fqdn:properties.configuration.ingress.fqdn,provisioningState:properties.provisioningState}}'"
            result = self.run_command(cmd)
            
            if result["success"]:
                try:
                    app_info = json.loads(result["stdout"])
                    fqdn = app_info.get("fqdn")
                    state = app_info.get("provisioningState")
                    
                    if fqdn and state == "Succeeded":
                        app_urls[app] = f"https://{fqdn}"
                        print(f"  ✅ {app}: {app_urls[app]}")
                    else:
                        print(f"  ❌ {app}: Not ready (state: {state})")
                        self.results["tests_failed"] += 1
                        return False
                        
                except json.JSONDecodeError:
                    print(f"  ❌ {app}: Failed to parse app info")
                    self.results["tests_failed"] += 1
                    return False
            else:
                print(f"  ❌ {app}: Failed to get app info")
                self.results["tests_failed"] += 1
                return False
        
        self.results["endpoints"] = app_urls
        self.results["tests_passed"] += 1
        return True

    async def validate_databases(self) -> bool:
        """Validate database connectivity"""
        print("🗄️ Validating databases...")
        
        # Check SQL Server
        cmd = f"az sql server show --name pathfinder-sql --resource-group {self.resource_group} --query '{{state:state,fullyQualifiedDomainName:fullyQualifiedDomainName}}'"
        result = self.run_command(cmd)
        
        if result["success"]:
            try:
                sql_info = json.loads(result["stdout"])
                if sql_info.get("state") == "Ready":
                    print(f"  ✅ SQL Server: {sql_info.get('fullyQualifiedDomainName')}")
                else:
                    print(f"  ❌ SQL Server not ready: {sql_info.get('state')}")
                    self.results["tests_failed"] += 1
                    return False
            except json.JSONDecodeError:
                print("  ❌ Failed to parse SQL Server info")
                self.results["tests_failed"] += 1
                return False
        else:
            print("  ❌ Failed to get SQL Server info")
            self.results["tests_failed"] += 1
            return False
        
        # Check Cosmos DB
        cmd = f"az cosmosdb list --resource-group {self.resource_group} --query '[0].{{name:name,provisioningState:provisioningState}}'"
        result = self.run_command(cmd)
        
        if result["success"]:
            try:
                cosmos_info = json.loads(result["stdout"])
                if cosmos_info and cosmos_info.get("provisioningState") == "Succeeded":
                    print(f"  ✅ Cosmos DB: {cosmos_info.get('name')}")
                    self.results["tests_passed"] += 1
                    return True
                else:
                    print(f"  ❌ Cosmos DB not ready: {cosmos_info}")
                    self.results["tests_failed"] += 1
                    return False
            except json.JSONDecodeError:
                print("  ❌ Failed to parse Cosmos DB info")
                self.results["tests_failed"] += 1
                return False
        else:
            print("  ❌ Failed to get Cosmos DB info")
            self.results["tests_failed"] += 1
            return False

    async def validate_security(self) -> bool:
        """Validate security configuration"""
        print("🔐 Validating security configuration...")
        
        # Check Key Vault
        cmd = f"az keyvault list --resource-group {self.resource_group} --query '[0].{{name:name,properties:properties}}'"
        result = self.run_command(cmd)
        
        if result["success"]:
            try:
                kv_info = json.loads(result["stdout"])
                if kv_info and kv_info.get("name"):
                    print(f"  ✅ Key Vault: {kv_info.get('name')}")
                    self.results["tests_passed"] += 1
                    return True
                else:
                    print("  ❌ Key Vault not found")
                    self.results["tests_failed"] += 1
                    return False
            except json.JSONDecodeError:
                print("  ❌ Failed to parse Key Vault info")
                self.results["tests_failed"] += 1
                return False
        else:
            print("  ❌ Failed to get Key Vault info")
            self.results["tests_failed"] += 1
            return False

    async def validate_monitoring(self) -> bool:
        """Validate monitoring setup"""
        print("📊 Validating monitoring setup...")
        
        # Check Application Insights
        cmd = f"az monitor app-insights component show --app pathfinder-insights --resource-group {self.resource_group} --query '{{name:name,provisioningState:provisioningState,instrumentationKey:instrumentationKey}}'"
        result = self.run_command(cmd)
        
        if result["success"]:
            try:
                ai_info = json.loads(result["stdout"])
                if ai_info.get("provisioningState") == "Succeeded":
                    print(f"  ✅ Application Insights: {ai_info.get('name')}")
                    self.results["tests_passed"] += 1
                    return True
                else:
                    print(f"  ❌ Application Insights not ready: {ai_info.get('provisioningState')}")
                    self.results["tests_failed"] += 1
                    return False
            except json.JSONDecodeError:
                print("  ❌ Failed to parse Application Insights info")
                self.results["tests_failed"] += 1
                return False
        else:
            print("  ❌ Failed to get Application Insights info")
            self.results["tests_failed"] += 1
            return False

    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("🚀 Starting Pathfinder Production Deployment Validation")
        print("=" * 60)
        print()
        
        validation_steps = [
            ("Azure Resources", self.validate_azure_resources),
            ("Container Apps", self.validate_container_apps),
            ("Databases", self.validate_databases),
            ("Security", self.validate_security),
            ("Monitoring", self.validate_monitoring),
        ]
        
        overall_success = True
        
        for step_name, step_func in validation_steps:
            print(f"Running {step_name} validation...")
            try:
                success = await step_func()
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"  ❌ {step_name} validation failed with exception: {e}")
                self.results["tests_failed"] += 1
                overall_success = False
            print()
        
        # Generate recommendations
        if self.results["tests_failed"] > 0:
            self.results["recommendations"].extend([
                "Review Azure portal for resource deployment status",
                "Check Container Apps logs for startup issues",
                "Verify all environment variables are configured correctly",
                "Ensure placeholder container images are replaced with actual application images"
            ])
        
        if overall_success and self.results["tests_passed"] >= 4:
            self.results["deployment_status"] = "ready_for_application_deployment"
            self.results["recommendations"].extend([
                "Infrastructure is ready - proceed with application container deployment",
                "Configure CI/CD pipeline to deploy application containers",
                "Update Microsoft Entra External ID app registration with production URLs",
                "Configure production secrets in Azure Key Vault"
            ])
        elif self.results["tests_passed"] >= 3:
            self.results["deployment_status"] = "mostly_ready"
            self.results["recommendations"].append("Address remaining issues before application deployment")
        else:
            self.results["deployment_status"] = "needs_attention"
            self.results["recommendations"].append("Multiple issues need resolution before proceeding")
        
        return self.results

    def print_summary(self):
        """Print validation summary"""
        print("=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        print()
        
        print(f"Deployment Status: {self.results['deployment_status'].upper()}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print()
        
        if self.results["endpoints"]:
            print("🌐 Application Endpoints:")
            for app, url in self.results["endpoints"].items():
                print(f"  {app}: {url}")
            print()
        
        if self.results["recommendations"]:
            print("💡 Recommendations:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. {rec}")
            print()
        
        success_rate = self.results["tests_passed"] / (self.results["tests_passed"] + self.results["tests_failed"]) * 100 if (self.results["tests_passed"] + self.results["tests_failed"]) > 0 else 0
        
        if success_rate >= 80:
            print("✅ Infrastructure deployment validation PASSED")
            print("🚀 Ready to proceed with application deployment")
        elif success_rate >= 60:
            print("⚠️ Infrastructure deployment validation PARTIAL")
            print("🔧 Address issues before proceeding")
        else:
            print("❌ Infrastructure deployment validation FAILED")
            print("🛠️ Critical issues must be resolved")

async def main():
    """Main validation function"""
    validator = ProductionValidator()
    
    try:
        results = await validator.run_validation()
        validator.print_summary()
        
        # Save results to file
        with open("production-validation-results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: production-validation-results.json")
        
        # Exit with appropriate code
        if results["deployment_status"] in ["ready_for_application_deployment", "mostly_ready"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

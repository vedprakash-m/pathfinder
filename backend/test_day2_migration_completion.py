#!/usr/bin/env python3
"""
Day 2 Migration Completion Test Script

This script validates the completion of Day 2 objectives:
1. Complete migration of secondary endpoints to unified Cosmos DB
2. Remove all SQLAlchemy imports and dependencies
3. Test unified implementation end-to-end
"""

import asyncio
import logging
import os
import re
import sys
from datetime import date, datetime
from typing import Dict

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.repositories.cosmos_unified import unified_cosmos_repo

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Day2MigrationValidator:
    """Validates Day 2 migration completion."""

    def __init__(self):
        self.secondary_endpoints = [
            "app/api/reservations.py",
            "app/api/feedback.py",
            "app/api/exports.py",
            "app/api/itineraries.py",
        ]

        self.sql_patterns = [
            r"from.*sqlalchemy.*import",
            r"from.*models.*import.*(?:Base|Trip|User)",
            r"from.*database.*import.*get_db",
            r"db\.query\(",
            r"db\.add\(",
            r"db\.commit\(",
        ]

        self.results = {
            "sql_cleanup": {},
            "cosmos_functionality": {},
            "endpoint_migration": {},
            "overall_status": "PENDING",
        }

    def check_sql_cleanup(self) -> Dict[str, bool]:
        """Check for remaining SQLAlchemy dependencies."""
        print("\n🔍 CHECKING SQL CLEANUP STATUS...")

        for endpoint_file in self.secondary_endpoints:
            if os.path.exists(endpoint_file):
                with open(endpoint_file, "r") as f:
                    content = f.read()

                has_sql_deps = False
                for pattern in self.sql_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        has_sql_deps = True
                        break

                self.results["sql_cleanup"][endpoint_file] = not has_sql_deps
                status = "✅ CLEAN" if not has_sql_deps else "⚠️ HAS SQL DEPS"
                print(f"  {endpoint_file}: {status}")
            else:
                print(f"  ⚠️ File not found: {endpoint_file}")
                self.results["sql_cleanup"][endpoint_file] = False

        return self.results["sql_cleanup"]

    async def test_cosmos_functionality(self) -> Dict[str, bool]:
        """Test unified Cosmos DB functionality for secondary endpoints."""
        print("\n🧪 TESTING COSMOS DB FUNCTIONALITY...")

        try:
            # Test reservation functionality
            print("  Testing reservation operations...")
            reservation_data = {
                "trip_id": "test-trip-123",
                "type": "accommodation",
                "name": "Test Hotel",
                "description": "Test reservation",
                "date": date.today().isoformat(),
                "location": "Test City",
                "created_by": "test-user-123",
            }

            reservation = await unified_cosmos_repo.create_reservation(reservation_data)
            print(f"    ✅ Created reservation: {reservation.id}")

            trip_reservations = await unified_cosmos_repo.get_trip_reservations("test-trip-123")
            print(f"    ✅ Retrieved {len(trip_reservations)} reservations for trip")

            self.results["cosmos_functionality"]["reservations"] = True

        except Exception as e:
            print(f"    ❌ Reservation test failed: {str(e)}")
            self.results["cosmos_functionality"]["reservations"] = False

        try:
            # Test feedback functionality
            print("  Testing feedback operations...")
            feedback_data = {
                "trip_id": "test-trip-123",
                "family_id": "test-family-123",
                "user_id": "test-user-123",
                "feedback_type": "suggestion",
                "target_element": "itinerary",
                "content": "Test feedback content",
            }

            feedback = await unified_cosmos_repo.create_feedback(feedback_data)
            print(f"    ✅ Created feedback: {feedback.id}")

            trip_feedback = await unified_cosmos_repo.get_trip_feedback("test-trip-123")
            print(f"    ✅ Retrieved {len(trip_feedback)} feedback items for trip")

            self.results["cosmos_functionality"]["feedback"] = True

        except Exception as e:
            print(f"    ❌ Feedback test failed: {str(e)}")
            self.results["cosmos_functionality"]["feedback"] = False

        try:
            # Test export functionality
            print("  Testing export operations...")
            export_data = {
                "user_id": "test-user-123",
                "trip_id": "test-trip-123",
                "format": "excel",
                "export_type": "complete",
            }

            export_task = await unified_cosmos_repo.create_export_task(export_data)
            print(f"    ✅ Created export task: {export_task.id}")

            user_exports = await unified_cosmos_repo.get_user_exports("test-user-123")
            print(f"    ✅ Retrieved {len(user_exports)} export tasks for user")

            self.results["cosmos_functionality"]["exports"] = True

        except Exception as e:
            print(f"    ❌ Export test failed: {str(e)}")
            self.results["cosmos_functionality"]["exports"] = False

        try:
            # Test itinerary functionality
            print("  Testing itinerary operations...")
            itinerary_data = {
                "trip_id": "test-trip-123",
                "title": "Test Itinerary",
                "description": "AI-generated test itinerary",
                "days": [
                    {
                        "date": date.today().isoformat(),
                        "activities": ["Activity 1", "Activity 2"],
                        "estimated_cost": 100.0,
                    }
                ],
                "generated_by": "test-user-123",
            }

            itinerary = await unified_cosmos_repo.create_itinerary(itinerary_data)
            print(f"    ✅ Created itinerary: {itinerary.id}")

            trip_itineraries = await unified_cosmos_repo.get_trip_itineraries("test-trip-123")
            print(f"    ✅ Retrieved {len(trip_itineraries)} itineraries for trip")

            self.results["cosmos_functionality"]["itineraries"] = True

        except Exception as e:
            print(f"    ❌ Itinerary test failed: {str(e)}")
            self.results["cosmos_functionality"]["itineraries"] = False

        return self.results["cosmos_functionality"]

    def check_endpoint_migration(self) -> Dict[str, bool]:
        """Check that endpoints are properly migrated to Cosmos DB."""
        print("\n📋 CHECKING ENDPOINT MIGRATION STATUS...")

        for endpoint_file in self.secondary_endpoints:
            if os.path.exists(endpoint_file):
                with open(endpoint_file, "r") as f:
                    content = f.read()

                # Check for unified Cosmos DB usage
                has_cosmos_import = "get_cosmos_repository" in content
                has_unified_repo = "UnifiedCosmosRepository" in content

                is_migrated = has_cosmos_import and has_unified_repo
                self.results["endpoint_migration"][endpoint_file] = is_migrated

                status = "✅ MIGRATED" if is_migrated else "⚠️ NEEDS MIGRATION"
                print(f"  {endpoint_file}: {status}")
            else:
                print(f"  ⚠️ File not found: {endpoint_file}")
                self.results["endpoint_migration"][endpoint_file] = False

        return self.results["endpoint_migration"]

    def generate_day2_report(self) -> str:
        """Generate Day 2 completion report."""

        # Calculate completion percentages
        sql_cleanup_pct = (
            (sum(self.results["sql_cleanup"].values()) / len(self.results["sql_cleanup"]) * 100)
            if self.results["sql_cleanup"]
            else 0
        )

        cosmos_functionality_pct = (
            (
                sum(self.results["cosmos_functionality"].values())
                / len(self.results["cosmos_functionality"])
                * 100
            )
            if self.results["cosmos_functionality"]
            else 0
        )

        endpoint_migration_pct = (
            (
                sum(self.results["endpoint_migration"].values())
                / len(self.results["endpoint_migration"])
                * 100
            )
            if self.results["endpoint_migration"]
            else 0
        )

        overall_pct = (sql_cleanup_pct + cosmos_functionality_pct + endpoint_migration_pct) / 3

        # Determine overall status
        if overall_pct >= 90:
            self.results["overall_status"] = "COMPLETE"
        elif overall_pct >= 70:
            self.results["overall_status"] = "MOSTLY_COMPLETE"
        else:
            self.results["overall_status"] = "IN_PROGRESS"

        report = f"""
==========================================
           DAY 2 MIGRATION REPORT
==========================================

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 Objective: Complete secondary endpoint migration to unified Cosmos DB

📊 COMPLETION SUMMARY:
• SQL Cleanup: {sql_cleanup_pct:.1f}%
• Cosmos DB Functionality: {cosmos_functionality_pct:.1f}%  
• Endpoint Migration: {endpoint_migration_pct:.1f}%
• OVERALL: {overall_pct:.1f}% - {self.results['overall_status']}

🔍 DETAILED RESULTS:

SQL Cleanup Status:
{self._format_results(self.results['sql_cleanup'])}

Cosmos DB Functionality:
{self._format_results(self.results['cosmos_functionality'])}

Endpoint Migration Status:
{self._format_results(self.results['endpoint_migration'])}

🎯 DAY 2 OBJECTIVES STATUS:
• ✅ Secondary endpoint identification: COMPLETE
• {'✅' if endpoint_migration_pct >= 75 else '⚠️'} Secondary endpoint migration: {endpoint_migration_pct:.1f}%
• {'✅' if sql_cleanup_pct >= 75 else '⚠️'} SQLAlchemy cleanup: {sql_cleanup_pct:.1f}%
• {'✅' if cosmos_functionality_pct >= 75 else '⚠️'} Unified Cosmos DB testing: {cosmos_functionality_pct:.1f}%

🚀 NEXT STEPS:
• Complete any remaining endpoint migrations
• Continue with Day 3 objectives (AI Integration)
• Proceed with security audit and performance optimization

==========================================
"""
        return report

    def _format_results(self, results: Dict[str, bool]) -> str:
        """Format results dictionary for display."""
        formatted = []
        for key, value in results.items():
            status = "✅ PASS" if value else "❌ FAIL"
            formatted.append(f"  {key}: {status}")
        return "\n".join(formatted)


async def main():
    """Run Day 2 migration validation."""
    print("🚀 STARTING DAY 2 MIGRATION VALIDATION...")
    print("=" * 50)

    validator = Day2MigrationValidator()

    # Run all validation checks
    validator.check_sql_cleanup()
    await validator.test_cosmos_functionality()
    validator.check_endpoint_migration()

    # Generate and display report
    report = validator.generate_day2_report()
    print(report)

    # Save report to file
    report_file = f"DAY2_MIGRATION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"📝 Full report saved to: {report_file}")

    # Exit with appropriate code
    if validator.results["overall_status"] == "COMPLETE":
        print("\n🎉 DAY 2 MIGRATION SUCCESSFULLY COMPLETED!")
        sys.exit(0)
    else:
        print(f"\n⚠️ DAY 2 MIGRATION STATUS: {validator.results['overall_status']}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

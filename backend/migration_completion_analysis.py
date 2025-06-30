#!/usr/bin/env python3
"""
Migration Completion Analysis Script

Analyzes the current state of the Cosmos DB migration and provides a detailed
action plan for completing the remaining work.
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Tuple

def analyze_api_file(file_path: str) -> Dict[str, any]:
    """Analyze an API file for migration status."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    file_name = os.path.basename(file_path)
    
    # Check for Cosmos DB usage
    has_cosmos_import = 'get_cosmos_repository' in content
    has_cosmos_dependency = 'UnifiedCosmosRepository' in content
    
    # Check for SQL usage
    has_sql_import = 'get_db' in content and 'from' in content
    sql_endpoints = len(re.findall(r'Depends\(get_db\)', content))
    session_deps = len(re.findall(r'Session.*=.*Depends\(get_db\)', content))
    
    # Count total endpoints
    total_endpoints = len(re.findall(r'@router\.(get|post|put|delete|patch)', content))
    
    # Migration status
    if has_cosmos_import and sql_endpoints == 0:
        status = "FULLY_MIGRATED"
    elif has_cosmos_import and sql_endpoints > 0:
        status = "PARTIALLY_MIGRATED"
    elif sql_endpoints > 0:
        status = "NEEDS_MIGRATION"
    else:
        status = "NO_DATABASE_USAGE"
    
    return {
        'file': file_name,
        'path': file_path,
        'status': status,
        'total_endpoints': total_endpoints,
        'sql_endpoints': sql_endpoints,
        'has_cosmos': has_cosmos_import,
        'has_sql': has_sql_import,
        'priority': get_priority(file_name)
    }

def get_priority(file_name: str) -> str:
    """Determine priority level for migration."""
    critical_apis = ['auth.py', 'families.py', 'trips.py', 'polls.py', 'assistant.py', 'consensus.py']
    high_apis = ['websocket.py', 'notifications.py', 'trip_messages.py']
    medium_apis = ['itineraries.py', 'coordination.py', 'reservations.py']
    
    if file_name in critical_apis:
        return "CRITICAL"
    elif file_name in high_apis:
        return "HIGH"
    elif file_name in medium_apis:
        return "MEDIUM"
    else:
        return "LOW"

def main():
    """Main analysis function."""
    print("🔍 COSMOS DB MIGRATION COMPLETION ANALYSIS")
    print("=" * 60)
    
    # Find all API files
    api_files = glob.glob("app/api/*.py")
    api_files = [f for f in api_files if not f.endswith('__init__.py')]
    
    results = []
    for file_path in api_files:
        try:
            result = analyze_api_file(file_path)
            results.append(result)
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    # Sort by priority and status
    priority_order = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
    status_order = {"NEEDS_MIGRATION": 1, "PARTIALLY_MIGRATED": 2, "FULLY_MIGRATED": 3, "NO_DATABASE_USAGE": 4}
    
    results.sort(key=lambda x: (priority_order[x['priority']], status_order[x['status']]))
    
    # Summary statistics
    total_files = len(results)
    fully_migrated = len([r for r in results if r['status'] == 'FULLY_MIGRATED'])
    partially_migrated = len([r for r in results if r['status'] == 'PARTIALLY_MIGRATED'])
    needs_migration = len([r for r in results if r['status'] == 'NEEDS_MIGRATION'])
    no_db = len([r for r in results if r['status'] == 'NO_DATABASE_USAGE'])
    
    print(f"\n📊 MIGRATION STATUS SUMMARY")
    print(f"Total API files analyzed: {total_files}")
    print(f"✅ Fully migrated: {fully_migrated}")
    print(f"🔄 Partially migrated: {partially_migrated}")
    print(f"❌ Needs migration: {needs_migration}")
    print(f"🔘 No database usage: {no_db}")
    
    completion_percentage = ((fully_migrated + (partially_migrated * 0.5)) / total_files) * 100
    print(f"🎯 Overall completion: {completion_percentage:.1f}%")
    
    print(f"\n🎯 DETAILED ANALYSIS BY PRIORITY")
    print("-" * 60)
    
    current_priority = None
    for result in results:
        if result['priority'] != current_priority:
            current_priority = result['priority']
            print(f"\n{current_priority} PRIORITY:")
        
        status_emoji = {
            'FULLY_MIGRATED': '✅',
            'PARTIALLY_MIGRATED': '🔄',
            'NEEDS_MIGRATION': '❌',
            'NO_DATABASE_USAGE': '🔘'
        }
        
        emoji = status_emoji[result['status']]
        endpoints_info = f"({result['total_endpoints']} endpoints"
        if result['sql_endpoints'] > 0:
            endpoints_info += f", {result['sql_endpoints']} need migration"
        endpoints_info += ")"
        
        print(f"  {emoji} {result['file']:<20} {result['status']:<20} {endpoints_info}")
    
    # Action plan
    print(f"\n🚀 RECOMMENDED ACTION PLAN")
    print("-" * 60)
    
    # Critical files that need work
    critical_work = [r for r in results if r['priority'] == 'CRITICAL' and r['status'] in ['NEEDS_MIGRATION', 'PARTIALLY_MIGRATED']]
    if critical_work:
        print(f"1. COMPLETE CRITICAL ENDPOINTS:")
        for item in critical_work:
            action = "migrate" if item['status'] == 'NEEDS_MIGRATION' else "finish migrating"
            print(f"   - {action} {item['file']} ({item['sql_endpoints']} endpoints)")
    
    # High priority files
    high_work = [r for r in results if r['priority'] == 'HIGH' and r['status'] in ['NEEDS_MIGRATION', 'PARTIALLY_MIGRATED']]
    if high_work:
        print(f"2. COMPLETE HIGH PRIORITY ENDPOINTS:")
        for item in high_work:
            action = "migrate" if item['status'] == 'NEEDS_MIGRATION' else "finish migrating"
            print(f"   - {action} {item['file']} ({item['sql_endpoints']} endpoints)")
    
    # Estimate remaining work
    total_sql_endpoints = sum(r['sql_endpoints'] for r in results)
    critical_sql = sum(r['sql_endpoints'] for r in critical_work)
    high_sql = sum(r['sql_endpoints'] for r in high_work)
    
    print(f"\n⏱️  EFFORT ESTIMATION:")
    print(f"Total SQL endpoints remaining: {total_sql_endpoints}")
    print(f"Critical priority endpoints: {critical_sql}")
    print(f"High priority endpoints: {high_sql}")
    print(f"Estimated time (5 min/endpoint): {total_sql_endpoints * 5} minutes ({total_sql_endpoints * 5 // 60}h {total_sql_endpoints * 5 % 60}m)")
    
    # Next steps
    print(f"\n✅ IMMEDIATE NEXT STEPS (Day 1 completion):")
    print(f"1. Complete families.py invitation endpoints (estimated 20 minutes)")
    print(f"2. Migrate assistant.py - critical AI endpoint (estimated 25 minutes)")
    print(f"3. Complete consensus.py and notifications.py partial migrations (estimated 30 minutes)")
    print(f"4. Test unified implementation end-to-end")
    print(f"5. Remove SQL imports and dependencies")
    
    print(f"\n🎯 TARGET: Complete critical/high priority endpoints = DAY 1 SUCCESS!")

if __name__ == "__main__":
    main()

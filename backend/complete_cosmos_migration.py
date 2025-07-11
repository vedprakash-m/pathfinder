#!/usr/bin/env python3
"""
Complete the migration of remaining API files to unified Cosmos DB.
This addresses the Day 4 security audit finding that only 63.6% of API files use Cosmos DB.
"""

import os
import re


def migrate_file_to_cosmos(filepath):
    """Migrate a single file from get_db to unified Cosmos DB"""
    print(f"Migrating {filepath}...")

    with open(filepath, "r") as f:
        content = f.read()

    original_content = content

    # Replace get_db dependency with get_cosmos_repository
    pattern1 = r"db: (AsyncSession|Session) = Depends\(get_db\)"
    replacement1 = (
        r"cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)"
    )
    content = re.sub(pattern1, replacement1, content)

    # Replace service instantiations that use db parameter
    # Look for common patterns like Service(db) and replace with Service(cosmos_repo)
    patterns_to_replace = [
        (r"Service\(db\)", "Service(cosmos_repo)"),
        (r"service = \w+\(db\)", lambda m: m.group(0).replace("(db)", "(cosmos_repo)")),
        (r"await \w+\(db,", lambda m: m.group(0).replace("(db,", "(cosmos_repo,")),
    ]

    for pattern, replacement in patterns_to_replace:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            content = re.sub(pattern, replacement, content)

    # Check if we need to add the import for UnifiedCosmosRepository
    if "UnifiedCosmosRepository" not in content and "get_cosmos_repository" in content:
        # Add import after the existing imports
        import_pattern = r"(from \.\.repositories\.cosmos_unified import.*)"
        if re.search(import_pattern, content):
            # Already has the import, might need to add UnifiedCosmosRepository
            content = re.sub(
                r"(from \.\.repositories\.cosmos_unified import [^)]*)",
                r"\1, UnifiedCosmosRepository",
                content,
            )
        else:
            # Add the import
            core_import_pattern = (
                r"(from \.\.core\.database_unified import get_cosmos_repository)"
            )
            if re.search(core_import_pattern, content):
                content = re.sub(
                    core_import_pattern,
                    r"\1\nfrom ..repositories.cosmos_unified import UnifiedCosmosRepository",
                    content,
                )

    # Check if we need to add the get_cosmos_repository import
    if (
        "get_cosmos_repository" in content
        and "from ..core.database_unified import get_cosmos_repository" not in content
    ):
        # Add the import after other core imports
        insert_after = r"(from fastapi import.*?\n)"
        if re.search(insert_after, content, re.DOTALL):
            content = re.sub(
                insert_after,
                r"\1from ..core.database_unified import get_cosmos_repository\n",
                content,
                count=1,
            )

    # Only write if changes were made
    if content != original_content:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"✅ Updated {filepath}")
        return True
    else:
        print(f"⚠️ No changes needed for {filepath}")
        return False


def main():
    """Main migration function"""
    api_files = [
        "app/api/coordination.py",
        "app/api/exports.py",
        "app/api/feedback.py",
        "app/api/itineraries.py",
        "app/api/reservations.py",
    ]

    backend_path = "/Users/vedprakashmishra/pathfinder/backend"
    updated_files = []

    for api_file in api_files:
        filepath = os.path.join(backend_path, api_file)
        if os.path.exists(filepath):
            if migrate_file_to_cosmos(filepath):
                updated_files.append(api_file)
        else:
            print(f"❌ File not found: {filepath}")

    print("\n🎯 Migration Summary:")
    print(f"✅ Updated {len(updated_files)} files")
    for file in updated_files:
        print(f"   - {file}")

    if updated_files:
        print("\n🚀 Next steps:")
        print("1. Review the changes in the updated files")
        print("2. Run tests to ensure functionality")
        print("3. Run security audit again to verify improved Cosmos DB usage")


if __name__ == "__main__":
    main()

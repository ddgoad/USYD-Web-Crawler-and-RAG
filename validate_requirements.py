#!/usr/bin/env python3
"""
Validate requirements.txt for potential dependency conflicts and issues.
"""

import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

def parse_requirements(file_path: str) -> Dict[str, List[str]]:
    """Parse requirements.txt and return a dict of package names to their version specs."""
    packages = defaultdict(list)
    
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse package specification
                # Handle == >= <= > < != ~= 
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)([><=!~]+[0-9\.\*]+.*)?', line)
                if match:
                    package_name = match.group(1).lower()
                    version_spec = match.group(2) if match.group(2) else ""
                    packages[package_name].append((line_num, line, version_spec))
                else:
                    print(f"⚠️  Line {line_num}: Could not parse '{line}'")
    
    except FileNotFoundError:
        print(f"❌ Error: requirements.txt not found at {file_path}")
        sys.exit(1)
    
    return packages

def find_duplicates(packages: Dict[str, List[str]]) -> List[Tuple[str, List]]:
    """Find packages that are specified multiple times."""
    duplicates = []
    for package, specs in packages.items():
        if len(specs) > 1:
            duplicates.append((package, specs))
    return duplicates

def check_version_conflicts(packages: Dict[str, List[str]]) -> List[Tuple[str, List]]:
    """Check for obvious version conflicts (exact version pins that differ)."""
    conflicts = []
    for package, specs in packages.items():
        if len(specs) > 1:
            # Check if there are conflicting exact version pins
            exact_versions = []
            for line_num, line, version_spec in specs:
                if version_spec and version_spec.startswith('=='):
                    version = version_spec[2:]
                    exact_versions.append((line_num, version))
            
            if len(exact_versions) > 1:
                # Check if all exact versions are the same
                versions = [v[1] for v in exact_versions]
                if len(set(versions)) > 1:
                    conflicts.append((package, specs))
    
    return conflicts

def check_known_problematic_combinations(packages: Dict[str, List[str]]) -> List[str]:
    """Check for known problematic package combinations."""
    warnings = []
    
    # Check crawl4ai specific issues
    if 'crawl4ai' in packages and 'litellm' in packages:
        crawl4ai_specs = packages['crawl4ai']
        litellm_specs = packages['litellm']
        
        # Check if crawl4ai==0.3.0 is used with incompatible litellm
        for _, line, version_spec in crawl4ai_specs:
            if version_spec == '==0.3.0':
                for _, litellm_line, litellm_version in litellm_specs:
                    if litellm_version and litellm_version.startswith('>=1.53'):
                        warnings.append(f"⚠️  crawl4ai==0.3.0 may be incompatible with {litellm_line}")
                    elif litellm_version == '==1.48.0':
                        print(f"✅ crawl4ai==0.3.0 correctly paired with litellm==1.48.0")
    
    # Add more known issue checks here
    return warnings

def main():
    print("🔍 Validating requirements.txt...")
    print("=" * 50)
    
    packages = parse_requirements('requirements.txt')
    
    # Check for duplicates
    duplicates = find_duplicates(packages)
    if duplicates:
        print("❌ DUPLICATE PACKAGES FOUND:")
        for package, specs in duplicates:
            print(f"   📦 {package}:")
            for line_num, line, version_spec in specs:
                print(f"      Line {line_num}: {line}")
        print()
    else:
        print("✅ No duplicate packages found")
    
    # Check for version conflicts
    conflicts = check_version_conflicts(packages)
    if conflicts:
        print("❌ VERSION CONFLICTS FOUND:")
        for package, specs in conflicts:
            print(f"   📦 {package}:")
            for line_num, line, version_spec in specs:
                print(f"      Line {line_num}: {line}")
        print()
    else:
        print("✅ No obvious version conflicts found")
    
    # Check for known problematic combinations
    warnings = check_known_problematic_combinations(packages)
    if warnings:
        print("⚠️  POTENTIAL ISSUES:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    # Summary
    total_packages = len(packages)
    print(f"📊 SUMMARY:")
    print(f"   • Total unique packages: {total_packages}")
    print(f"   • Duplicate entries: {len(duplicates)}")
    print(f"   • Version conflicts: {len(conflicts)}")
    print(f"   • Potential issues: {len(warnings)}")
    
    if duplicates or conflicts:
        print("\n❌ Issues found - please fix before deployment")
        sys.exit(1)
    else:
        print("\n✅ Requirements.txt validation passed!")

if __name__ == "__main__":
    main()

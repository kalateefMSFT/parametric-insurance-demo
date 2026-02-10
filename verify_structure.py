#!/usr/bin/env python3
"""
Project Structure Verification Script
Checks that all required files are present
"""
import os
import sys
from pathlib import Path

# Expected file structure
REQUIRED_FILES = {
    "Root": [
        ".env.example",
        "README.md",
        "DEPLOYMENT.md",
        "PROJECT_SUMMARY.md",
        "FILE_STRUCTURE.md"
    ],
    "shared": [
        "__init__.py",
        "config.py",
        "models.py",
        "fabric_client.py",
        "eventgrid_client.py"
    ],
    "functions": [
        "host.json",
        "requirements.txt"
    ],
    "functions/OutageMonitor": [
        "__init__.py",
        "function.json",
        "requirements.txt"
    ],
    "functions/ThresholdEvaluator": [
        "__init__.py",
        "function.json",
        "requirements.txt"
    ],
    "functions/PayoutProcessor": [
        "__init__.py",
        "function.json",
        "requirements.txt"
    ],
    "functions/OutageResolutionMonitor": [
        "__init__.py",
        "function.json",
        "requirements.txt"
    ],
    "foundry/agents": [
        "claims_validator_agent.py"
    ],
    "foundry/prompts": [
        "validation_prompt.txt"
    ],
    "fabric/notebooks": [
        "01_data_ingestion.py"
    ],
    "fabric/sql": [
        "create_warehouse_schema.sql",
        "sample_policies.sql"
    ],
    "fabric/pipelines": [
        "outage_ingestion_pipeline.json"
    ],
    "setup": [
        "azure-setup.sh",
        "requirements.txt"
    ],
    "demo": [
        "run_demo.py"
    ],
    "tests": [
        "run_tests.py",
        "test_outage_monitor.py",
        "test_threshold_evaluator.py",
        "test_payout_processor.py"
    ]
}


def verify_project_structure():
    """Verify all required files exist"""
    project_root = Path(__file__).parent
    
    print("="*70)
    print("PARAMETRIC INSURANCE DEMO - PROJECT VERIFICATION")
    print("="*70)
    print()
    
    all_files_present = True
    total_files = 0
    missing_files = []
    
    for directory, files in REQUIRED_FILES.items():
        if directory == "Root":
            dir_path = project_root
            display_path = "."
        else:
            dir_path = project_root / directory
            display_path = directory
        
        print(f"Checking {display_path}/")
        
        for file in files:
            total_files += 1
            file_path = dir_path / file
            
            if file_path.exists():
                print(f"  ✓ {file}")
            else:
                print(f"  ✗ {file} - MISSING")
                all_files_present = False
                missing_files.append(f"{display_path}/{file}")
        
        print()
    
    # Summary
    print("="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"Total expected files: {total_files}")
    print(f"Files found: {total_files - len(missing_files)}")
    
    if all_files_present:
        print("\n✓ All files present - Project structure is complete!")
        print()
        print("Next steps:")
        print("1. Review README.md for project overview")
        print("2. Follow DEPLOYMENT.md for setup instructions")
        print("3. Run: cd setup && ./azure-setup.sh")
        return 0
    else:
        print(f"\n✗ Missing {len(missing_files)} file(s):")
        for file in missing_files:
            print(f"  - {file}")
        return 1


if __name__ == "__main__":
    sys.exit(verify_project_structure())

#!/usr/bin/env python3
"""
Local test runner for JSON to C# Class Generator
Runs all tests and provides a summary.
"""

import subprocess
import sys
import os
import json

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} passed")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    """Run all tests and checks."""
    print("JSON to C# Class Generator - Test Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("json_to_csharp.py"):
        print("❌ Error: json_to_csharp.py not found. Run this script from the project root.")
        return 1
    
    # Install dependencies
    print("📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt", "Dependencies installation"):
        return 1
    
    results = []
    
    # Run unit tests
    results.append(run_command(
        "python -m pytest test_json_to_csharp.py -v",
        "Unit tests"
    ))
    
    # Run integration test
    print("\n🔄 Running integration test...")
    test_data = {
        "users": [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "isActive": True,
                "createdAt": "2023-01-15T10:30:00Z"
            }
        ],
        "totalCount": 1
    }
    
    with open("test_sample.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    integration_success = run_command(
        "python json_to_csharp.py test_sample.json --output test_output --namespace TestApp.Models --root-class TestDto",
        "Integration test - Generation"
    )
    
    if integration_success:
        # Check generated files
        expected_files = ["test_output/TestDto.cs", "test_output/User.cs"]
        files_exist = all(os.path.exists(f) for f in expected_files)
        
        if files_exist:
            print("✅ Generated files check passed")
            
            # Check content
            with open("test_output/TestDto.cs", "r") as f:
                content = f.read()
                content_checks = [
                    "namespace TestApp.Models" in content,
                    "public class TestDto" in content,
                    "List<User>?" in content,
                    "auto-generated" in content,
                    "github.com/tomikng/json-to-dotnet-classes" in content
                ]
                
                if all(content_checks):
                    print("✅ Generated content check passed")
                    integration_success = True
                else:
                    print("❌ Generated content check failed")
                    integration_success = False
        else:
            print("❌ Generated files check failed")
            integration_success = False
    
    results.append(integration_success)
    
    # Clean up
    print("\n🧹 Cleaning up...")
    cleanup_items = ["test_sample.json", "test_output", ".pytest_cache", "__pycache__"]
    for item in cleanup_items:
        if os.path.exists(item):
            if os.path.isdir(item):
                import shutil
                shutil.rmtree(item)
            else:
                os.remove(item)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    test_names = ["Unit Tests", "Integration Tests"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print(f"\n💥 {total - passed} test(s) failed. Please fix before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
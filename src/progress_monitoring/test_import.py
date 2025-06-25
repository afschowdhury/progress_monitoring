#!/usr/bin/env python3
"""
Test script to verify that the progress_monitoring package can be imported correctly.
"""

try:
    from progress_monitoring.factory import analyze_construction_progress
    print("✅ Successfully imported analyze_construction_progress from progress_monitoring.factory")
    
    from progress_monitoring import ConstructionSiteAnalyzer
    print("✅ Successfully imported ConstructionSiteAnalyzer from progress_monitoring")
    
    from progress_monitoring.config import AnalysisConfig, ModelProvider
    print("✅ Successfully imported config classes from progress_monitoring.config")
    
    print("\n🎉 All imports successful! The package is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure you've installed the package in development mode: pip install -e .")
    print("2. Make sure you're running this from the project root directory")
    print("3. Check that your Python environment has all required dependencies") 
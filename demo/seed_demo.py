"""
CLI script to wipe and seed demo data across all 3 ArcGIS Feature Layers.
Usage:
    python demo/seed_demo.py
"""

import sys
import os

# Add parent directory to sys.path if running directly as a script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from demo.seeder import reset_all_demo_data

if __name__ == "__main__":
    print("Starting ArcGIS QR Asset Tracking Demo Seeder...")
    result = reset_all_demo_data()
    print("Demo Seeding Complete!")
    print(result)

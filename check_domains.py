#!/usr/bin/env python3
"""
Quick script to check domain distribution in raw data.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from storage.database import db_manager
from storage.models import RawData

def check_domain_distribution():
    """Check how data is distributed across domains."""
    print("🌍 Checking Domain Distribution in Raw Data")
    print("=" * 50)
    
    try:
        with db_manager.get_session() as session:
            # Get all raw data items
            raw_items = session.query(RawData).all()
            
            print(f"📊 Total raw data items: {len(raw_items):,}")
            
            # Count by domain
            domain_counts = {}
            for item in raw_items:
                if item.metadata_json and 'domain' in item.metadata_json:
                    domain = item.metadata_json['domain']
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            print(f"\n📈 Domain Distribution:")
            print("-" * 30)
            
            total_items = sum(domain_counts.values())
            for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_items) * 100
                print(f"   • {domain}: {count:,} items ({percentage:.1f}%)")
            
            # Show what a 100-item sample would look like
            print(f"\n🎯 100-Item Sample Distribution (estimated):")
            print("-" * 45)
            
            for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
                sample_count = int((count / total_items) * 100)
                if sample_count > 0:
                    print(f"   • {domain}: ~{sample_count} items")
            
            # Check if we have enough items per domain for cross-paper analysis
            print(f"\n🔍 Cross-Paper Analysis Potential:")
            print("-" * 35)
            
            for domain, count in domain_counts.items():
                if count >= 2:
                    print(f"   ✅ {domain}: {count} items (can do cross-paper analysis)")
                else:
                    print(f"   ⚠️ {domain}: {count} items (insufficient for cross-paper)")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_domain_distribution()

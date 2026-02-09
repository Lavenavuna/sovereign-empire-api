# Add this near the top of your create-premium-content.py
import argparse

def main():
    parser = argparse.ArgumentParser(description='Generate premium content')
    parser.add_argument('business_type', help='Type of business')
    parser.add_argument('service_area', help='Service area/location')
    parser.add_argument('--jumpstart', action='store_true', help='Use Jumpstart package (3 posts)')
    
    args = parser.parse_args()
    
    # Then use args.jumpstart to determine package
    if args.jumpstart:
        blog_count = 3
        package_tier = "Jumpstart"
    else:
        blog_count = 5
        package_tier = "Dominance"
    
    # Rest of your code...

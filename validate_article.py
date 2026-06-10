#!/usr/bin/env python3
"""Validator for poradnik-samochodowy articles.

Checks:
- H2 sections (6-12+)
- Word count (1500+ for standard, 2500+ for long)
- Internal links (2+ minimum, ALL must be from sitemap)
- External links (2+ minimum)
- Strong tags (10+ minimum)
- FAQ items (5+ minimum)
- All internal links must exist in sitemap.html
"""

import sys
import re
from pathlib import Path
from html.parser import HTMLParser

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.internal_links = set()
        self.external_links = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    if value.startswith('/'):
                        self.internal_links.add(value)
                    elif value.startswith('http'):
                        self.external_links.add(value)

def extract_sitemap_links(sitemap_path):
    """Extract all article links from sitemap.html"""
    sitemap_links = set()
    try:
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all href="/..." in sitemap
        matches = re.findall(r'href="([^"]*)"', content)
        for match in matches:
            if match.startswith('/') and not match.endswith('.html'):
                sitemap_links.add(match)
            elif match.startswith('/') and match.endswith('.html'):
                sitemap_links.add(match)
    except FileNotFoundError:
        pass

    return sitemap_links

def verify_article(file_path, sitemap_path='sitemap.html'):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get actual sitemap directory
    if not Path(sitemap_path).is_absolute():
        sitemap_path = Path(file_path).parent.parent / sitemap_path

    # Extract links
    parser = LinkParser()
    parser.feed(content)
    internal_links = parser.internal_links
    external_links = parser.external_links

    # Get sitemap links
    sitemap_links = extract_sitemap_links(str(sitemap_path))

    # Basic counts
    h2_count = content.count('<h2>')
    h3_count = content.count('<h3>')
    strong_count = content.count('<strong>')
    faq_count = content.count('"@type": "Question"')
    word_count = len(content.split())

    failed = []

    # Validation checks
    if h2_count < 6:
        failed.append(f"❌ H2 sections: {h2_count} (need 6+)")

    if word_count < 1500:
        failed.append(f"❌ Word count: {word_count} (need 1500+)")

    if len(internal_links) < 2:
        failed.append(f"❌ Internal links: {len(internal_links)} (need 2+)")

    if len(external_links) < 2:
        failed.append(f"❌ External links: {len(external_links)} (need 2+)")

    if strong_count < 10:
        failed.append(f"❌ Strong tags: {strong_count} (need 10+)")

    if faq_count < 5:
        failed.append(f"❌ FAQ items: {faq_count} (need 5+)")

    # Check if internal links are from sitemap
    invalid_links = []
    for link in internal_links:
        # Skip certain meta links
        if link in ['/sitemap.html', '/blog.html', '/katalog/', '/']:
            continue

        # Check if link exists in sitemap
        # Match both with and without trailing slash
        normalized_link = link.rstrip('/')
        found = False
        for sitemap_link in sitemap_links:
            if sitemap_link.rstrip('/') == normalized_link:
                found = True
                break

        if not found and link != '/':
            invalid_links.append(link)

    if invalid_links:
        failed.append(f"❌ Links NOT in sitemap: {', '.join(invalid_links)}")

    # Print results
    if failed:
        print("❌ VALIDATION FAILED:")
        for issue in failed:
            print(f"  {issue}")
        print(f"\nℹ️  Sitemap contains {len(sitemap_links)} links")
        print(f"ℹ️  Article internal links: {internal_links}")
        return False

    print("✅ ALL CHECKS PASSED")
    print(f"  • H2 sections: {h2_count}")
    print(f"  • Internal links: {len(internal_links)} (all from sitemap ✓)")
    print(f"  • External links: {len(external_links)}")
    print(f"  • Strong tags: {strong_count}")
    print(f"  • Word count: {word_count}")
    print(f"  • FAQ items: {faq_count}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 validate_article.py <file.html> [sitemap.html]")
        sys.exit(1)

    file_path = sys.argv[1]
    sitemap = sys.argv[2] if len(sys.argv) > 2 else 'sitemap.html'

    success = verify_article(file_path, sitemap)
    sys.exit(0 if success else 1)

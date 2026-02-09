#!/usr/bin/env python3
"""
Web Crawler Word Extractor

Async web crawler that crawls a website starting from a given URL,
extracts all words from pages (letters only, lowercase),
removes duplicates, and outputs a sorted wordlist to a text file.
"""

import asyncio
import re
import argparse
import sys
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Note: 'tqdm' is not installed. Progress updates will be basic.")
    print("      For a better experience, install it with: pip install tqdm")
    print()


WORD_PATTERN = re.compile(r'[a-z]+')


def normalize_url(url):
    """Normalize URL by removing fragments and standardizing."""
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path + ("?" + parsed.query if parsed.query else "")


def extract_words(text):
    """Extract lowercase words containing only letters."""
    return set(WORD_PATTERN.findall(text.lower()))


def extract_links(soup, base_url):
    """Extract all href links from anchor tags."""
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        normalized = normalize_url(full_url)
        links.add(normalized)
    return links


async def crawl_url(client, url, semaphore):
    """Crawl a single URL, extract words and links. Returns (url, words, links)."""
    async with semaphore:
        try:
            response = await client.get(url, timeout=20.0, follow_redirects=True)
            response.raise_for_status()

            if 'text/html' not in response.headers.get('content-type', ''):
                return url, set(), set()

            soup = BeautifulSoup(response.content, 'lxml')

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.extract()

            text = soup.get_text(separator=' ')
            words = extract_words(text)

            links = extract_links(soup, url)

            return url, words, links

        except Exception:
            return url, set(), set()


async def crawl_async(start_url, max_depth, max_pages, workers):
    """Main async crawl function."""
    visited = set()
    queue = deque([(normalize_url(start_url), 0)])
    visited.add(normalize_url(start_url))
    all_words = set()

    semaphore = asyncio.Semaphore(workers)

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0)

    async with httpx.AsyncClient(http2=True, timeout=30.0, headers={'User-Agent': 'Mozilla/5.0'}, limits=limits) as client:
        pages_crawled = 0
        start_time = time.time()

        if HAS_TQDM:
            pbar = tqdm(total=max_pages, desc="Crawling", unit="page")
        else:
            pbar = None

        while queue and pages_crawled < max_pages:
            urls_to_crawl = []

            while queue and len(urls_to_crawl) < workers * 2:
                url, depth = queue.popleft()
                if depth > max_depth:
                    continue
                urls_to_crawl.append((url, depth))

            if not urls_to_crawl:
                break

            tasks = [crawl_url(client, url, semaphore) for url, _ in urls_to_crawl]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, tuple):
                    crawled_url, words, links = result
                    pages_crawled += 1
                    all_words.update(words)

                    for link in links:
                        if link not in visited and len(visited) < max_pages:
                            visited.add(link)
                            queue.append((link, 0))

                    if pbar:
                        pbar.update(1)
                        elapsed = time.time() - start_time
                        rate = pages_crawled / elapsed if elapsed > 0 else 0
                        pbar.set_postfix({"words": len(all_words), "rate": f"{rate:.1f}/s"})

        if pbar:
            pbar.close()

    return pages_crawled, all_words


def main():
    parser = argparse.ArgumentParser(description="Crawl a website and extract a lowercase wordlist.")
    parser.add_argument("url", help="Starting URL to crawl")
    parser.add_argument("-d", "--depth", type=int, default=3, help="Maximum crawl depth (default: 3)")
    parser.add_argument("-p", "--max-pages", type=int, default=10000, help="Maximum number of pages to crawl (default: 10000)")
    parser.add_argument("-f", "--file", type=str, default="wordlist.txt", help="Output filename for wordlist (default: wordlist.txt)")
    parser.add_argument("-w", "--workers", type=int, default=5, help="Number of concurrent workers (default: 5)")
    args = parser.parse_args()

    start_url = args.url
    max_depth = args.depth
    max_pages = args.max_pages
    output_file = args.file
    workers = args.workers

    print(f"Starting crawl from: {start_url}")
    print(f"Max depth: {max_depth}, Max pages: {max_pages}, Workers: {workers}")
    print("This may take a while for large sites...")

    pages_crawled, all_words = asyncio.run(crawl_async(start_url, max_depth, max_pages, workers))

    print(f"\nCrawl complete. Visited {pages_crawled} pages.")
    print(f"Found {len(all_words)} unique words.")

    sorted_words = sorted(all_words)
    with open(output_file, 'w') as f:
        for word in sorted_words:
            f.write(word + '\n')

    print(f"Wordlist saved to {output_file}")


if __name__ == "__main__":
    main()

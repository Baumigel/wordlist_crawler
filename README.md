# Web Crawler Word Extractor

Async web crawler that extracts all words from a website and saves them to a wordlist.

## Features

- Async HTTP/2 crawling for maximum speed
- Concurrent page processing
- Automatic deduplication
- Progress bar with ETA
- Configurable depth, page limit, and worker count
- Words extracted in lowercase (numbers and special characters removed)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python crawler_wordlist.py <url> [options]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-d, --depth` | Maximum crawl depth | 3 |
| `-p, --max-pages` | Maximum pages to crawl | 10000 |
| `-f, --file` | Output filename | wordlist.txt |
| `-w, --workers` | Concurrent workers | 5 |

### Examples

```bash
# Basic crawl
python crawler_wordlist.py https://example.com

# Crawl 100 pages with depth 2
python crawler_wordlist.py https://example.com -p 100 -d 2

# Custom output file
python crawler_wordlist.py https://example.com -f mywords.txt

# More workers for faster crawling
python crawler_wordlist.py https://example.com -w 10
```

## Requirements

- Python 3.8+
- httpx with HTTP/2 support
- lxml for fast HTML parsing
- beautifulsoup4
- tqdm for progress bar

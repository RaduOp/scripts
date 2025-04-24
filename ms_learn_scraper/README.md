# Microsoft Learn Scraper

A Python utility that fetches and processes articles from Microsoft Learn documentation based on search queries.

## Description

This tool allows you to search Microsoft Learn's documentation and extract relevant content from the search results. It uses Microsoft's public API to perform searches and then processes the results by extracting the main content from each article. The tool works concurrently to improve performance when processing multiple articles.

## Features

- Search Microsoft Learn documentation using keywords
- Extract and process article content, preserving the main text while removing irrelevant elements
- Convert HTML to Markdown format for better readability
- Process multiple articles concurrently for improved performance
- Show progress with a progress bar
- Save results in JSON format

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/scripts-collection.git
cd scripts-collection

# Install required packages
pip install -r requirements.txt
```

## Usage

```bash
python ms_learn_scraper.py --query "YOUR SEARCH QUERY" [OPTIONS]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--query` | Search query (required) | N/A |
| `--max-results` | Maximum number of results to fetch (1-30) | 15 |
| `--output-file` | Name of the output file (must end with .json) | `<query>.json` |
| `--output-folder` | Folder where the output file will be saved | `articles/` |
| `--max-workers` | Maximum number of concurrent workers (1-30) | 5 |

### Examples

Basic usage:
```bash
python ms_learn_scraper.py --query "Azure Functions"
```

Advanced usage:
```bash
python ms_learn_scraper.py --query "Azure Functions" --max-results 20 --output-file azure_functions_docs.json --output-folder my_research/ --max-workers 10
```

## Output

The script produces a JSON file with the following structure:

```json
{
  "articles": [
    {
      "title": "Article Title",
      "content": "Markdown-formatted content of the article",
      "reference": "URL of the original article"
    },
    // Additional articles...
  ]
}
```

## Limitations

- Maximum of 30 search results per query
- Only fetches documentation content (not tutorials, videos, etc.)
- Images are not preserved in the extracted content
- External links are removed from the content
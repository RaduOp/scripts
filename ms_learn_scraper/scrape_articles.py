import argparse
import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import html2text
from tqdm import tqdm


def search_ms_learn(query, max_results):
    # Search the Microsoft Learn documentation using their public API
    base_url = "https://learn.microsoft.com/api/search"
    params = {
        "search": query,
        "locale": "en-us",
        "facet": "category",
        "$filter": "category eq 'Documentation'",
        "$top": max_results,
    }

    try:
        response = requests.get(
            base_url, params=params, timeout=10
        )  # Timeout to avoid hanging
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Microsoft Learn: {e}")
        return []

    # Extract and return relevant information from the search results
    items = []
    for result in response.json().get("results", []):
        items.append(
            {
                "link": result["url"],
                "title": result["title"],
                "description": result["description"],
                "updated": result["lastUpdatedDate"],
            }
        )
    return items


def extract_content(url):
    # Fetch and parse a Microsoft Learn article
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

    # Only extracting main content and title
    # Images are being ignored
    # Elements such as code snippets and tabbed groups are being removed
    # Links that do not point back to ms learn are being removed
    try:
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1")
        content = soup.find_all("div", class_="content")[-1]

        # Remove specific unwanted elements from the content
        elements_to_remove = ["code", ".tabGroup"]
        for selector in elements_to_remove:
            for element in content.select(selector):
                element.decompose()

        # Remove links that don't point to learn.microsoft.com
        for a in content.find_all("a", href=True):
            domain = urlparse(a["href"]).netloc
            if "learn.microsoft.com" not in domain:
                a.unwrap()

        return {
            "title": "" if title is None else title.get_text(strip=True),
            "content": html2text.html2text(str(content)),
            "reference": url,
        }
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None


def run_script(query, max_results, max_workers):
    # Run the search and process each result concurrently
    search_results = search_ms_learn(query, max_results=max_results)

    if not search_results:
        print("No search results found. Exiting.")
        return []

    ms_articles = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Wrap the list of search results with tqdm to show progress as they're processed
        future_to_url = {
            executor.submit(extract_content, item["link"]): item["link"]
            for item in search_results
        }

        # Use tqdm to track progress while tasks are being completed
        with tqdm(total=len(future_to_url), desc="Processing articles") as pbar:
            for future in as_completed(future_to_url):
                try:
                    result = future.result(
                        timeout=30
                    )  # Timeout for the individual task
                    if result is not None:
                        ms_articles.append(result)
                except TimeoutError:
                    print(f"Timeout occurred while processing a URL.")
                except Exception as e:
                    print(f"Error during execution: {e}")
                finally:
                    pbar.update(1)  # Increment progress bar

    return ms_articles


def parse_args():
    # Helper to restrict integer arguments to a specific range
    def int_range(min_val, max_val):
        def checker(value):
            try:
                val = int(value)
                if val < min_val or val > max_val:
                    raise argparse.ArgumentTypeError(
                        f"Value must be between {min_val} and {max_val}"
                    )
                return val
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")

        return checker

    # Helper to ensure file name ends with .json
    def json_file(value):
        if not value.endswith(".json"):
            raise argparse.ArgumentTypeError("Output file must end with .json")
        return value

    # Helper to ensure folder path ends with /
    def folder(value):
        if not value.endswith("/"):
            raise argparse.ArgumentTypeError("Folder path must end with /")
        return value

    # Argument parsing and validation
    parser = argparse.ArgumentParser(description="Fetch articles from Microsoft Learn.")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument(
        "--max-results",
        default=15,
        type=int_range(1, 30),
        help="Maximum number of results to fetch",
    )
    parser.add_argument(
        "--output-file",
        type=json_file,
        help="Name of your file, will use the query as default",
    )
    parser.add_argument(
        "--output-folder",
        default="articles/",
        type=folder,
        help="A folder where the file will be saved",
    )
    parser.add_argument(
        "--max-workers",
        default=5,
        type=int_range(1, 30),
        help="Maximum number of workers",
    )

    args = parser.parse_args()

    # If no output file is specified, generate one from the query
    if not args.output_file:
        args.output_file = args.query.replace(" ", "_") + ".json"

    return args


if __name__ == "__main__":
    args = parse_args()

    try:
        # Collect results using the specified options
        results = run_script(
            args.query, max_results=args.max_results, max_workers=args.max_workers
        )

        # Ensure output folder exists
        if not os.path.isdir(args.output_folder):
            os.makedirs(args.output_folder)

        # Compose the full output path
        file_path = os.path.join(args.output_folder, args.output_file)

        # Save results to JSON file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"articles": results}, f, indent=4, ensure_ascii=False)
            print(f"Results saved to '{file_path}'")
        except IOError as e:
            print(f"Error writing to file '{file_path}': {e}")
    except Exception as e:
        print(f"Error during execution: {e}")

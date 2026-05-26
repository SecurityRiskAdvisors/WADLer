# Native & 3rd party imports
from dataclasses import dataclass
import json
from logging import Logger
import requests
import urllib3
from rich.table import Table
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel


@dataclass
class Utils:
    console: Console
    logger: Logger

    def save_file(self, path: str, content: str) -> None:
        try:
            with open(path, "w") as f:
                json.dump(content, f, indent=2)
                self.logger.info(f"Results saved to {path}")
        except Exception:
            self.logger.error(f"Failed to save file: {path}")

    def configure_session(self, args) -> requests.Session:
        """
        Configure a requests session based on command line arguments.

        Args:
            args: Command line arguments

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Setup proxies if configured
        if args.http_proxy or args.https_proxy:
            proxies = {}
            if args.http_proxy:
                proxies["http"] = args.http_proxy
            if args.https_proxy:
                proxies["https"] = args.https_proxy

            if proxies:
                session.proxies.update(proxies)
                self.logger.info(f"Using proxies: {proxies}")

        # Setup authentication if configured
        if args.username and args.password:
            session.auth = (args.username, args.password)
            self.logger.info(f"Using Basic Authentication for user: {args.username}.")
        elif args.token:
            session.headers.update({"Authorization": f"Bearer {args.token}"})
            self.logger.info("Using Bearer Token Authentication.")
        else:
            self.logger.info("No authentication credentials provided.")

        # Setup common headers
        session.headers.update({"User-Agent": args.user_agent, "Accept": args.accept})

        # Add extra headers if provided
        if args.header:
            for header in args.header:
                if ":" in header:
                    key, value = header.split(":", 1)
                    session.headers[key.strip()] = value.strip()

        # For extra safety, disable SSL warnings when verification is disabled
        if args.no_verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return session

    def generate_report(self, results: List[Dict[str, Any]]) -> None:
        """Generates and displays a report of the test results."""
        success_count = sum(1 for r in results if r.get("status_code", 500) < 400)
        client_error_count = sum(
            1 for r in results if 400 <= r.get("status_code", 0) < 500
        )
        server_error_count = sum(1 for r in results if r.get("status_code", 0) >= 500)
        error_count = sum(1 for r in results if "error" in r)

        # Create a summary table
        table = Table(title="API Test Summary")
        table.add_column("Category", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        total = len(results)
        table.add_row("Total Endpoints", str(total), "100%")
        table.add_row(
            "Successful (2xx/3xx)",
            str(success_count),
            f"{success_count/total*100:.1f}%" if total else "0%",
        )
        table.add_row(
            "Client Errors (4xx)",
            str(client_error_count),
            f"{client_error_count/total*100:.1f}%" if total else "0%",
        )
        table.add_row(
            "Server Errors (5xx)",
            str(server_error_count),
            f"{server_error_count/total*100:.1f}%" if total else "0%",
        )
        table.add_row(
            "Request Errors",
            str(error_count),
            f"{error_count/total*100:.1f}%" if total else "0%",
        )

        self.console.print(
            Panel(table, title="Test Results Summary", border_style="green")
        )

        # Detailed results table
        detail_table = Table(title="API Endpoint Results")
        detail_table.add_column("Method", style="bold")
        detail_table.add_column("Endpoint")
        detail_table.add_column("Status")
        detail_table.add_column("Response Time", justify="right")
        detail_table.add_column("Size", justify="right")

        for result in results:
            method = result.get("method", "ERROR")
            url = result.get("url", "N/A")

            if "error" in result:
                status = f"[red]Error: {result['error']}[/red]"
                response_time = "N/A"
                size = "N/A"
            else:
                status_code = result.get("status_code", 0)
                if status_code < 400:
                    status_style = "green"
                elif status_code < 500:
                    status_style = "yellow"
                else:
                    status_style = "red"
                status = f"[{status_style}]{status_code} {result.get('reason', '')}[/{status_style}]"
                response_time = f"{result.get('response_time', 0):.3f}s"
                size = f"{result.get('response_size', 0):,} bytes"

            detail_table.add_row(method, url, status, response_time, size)

        self.console.print(detail_table)

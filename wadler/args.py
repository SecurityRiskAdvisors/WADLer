# 3rd Party & native imports
from dataclasses import dataclass
import argparse
from logging import Logger


# Internal imports


@dataclass
class Args:
    logger: Logger

    def __post_init__(self):
        self.parser = argparse.ArgumentParser(
            description="The WADLer: WADL parser and API tester",
        )
        self._setup_arguments()

    def run(self):
        """
        Parses CLI args using argparse, returns a dict of CLI arguments
        """
        self.logger.info("Parsing CLI arguments")
        self.args = self.parser.parse_args()
        return self.args

    def _setup_arguments(self) -> None:
        """
        Configures Argparse arguments and groups
        """
        # Required arguments
        self.parser.add_argument("wadl_source", help="Path to WADL file or URL")

        # Output options
        self.parser.add_argument(
            "-o", "--output", help="Output file for results (JSON)"
        )
        self.parser.add_argument(
            "-v", "--verbose", action="store_true", help="Verbose output"
        )

        # Filter options
        filter_group = self.parser.add_argument_group("Filtering Options")
        filter_group.add_argument(
            "--endpoint",
            help="Only test endpoints containing this string (comma-separated for multiple)",
        )
        filter_group.add_argument(
            "--method",
            help="Only test these HTTP methods (comma-separated, e.g. GET,POST)",
        )

        # Proxy settings
        proxy_group = self.parser.add_argument_group(
            "Proxy Configuration",
            description="Proxying will be enabled if one or more proxy URLs are supplied.",
        )
        proxy_group.add_argument(
            "--http-proxy", help="HTTP proxy URL (e.g., http://proxy:8080)"
        )
        proxy_group.add_argument(
            "--https-proxy", help="HTTPS proxy URL (e.g., http://proxy:8080)"
        )

        # Authentication settings
        auth_group = self.parser.add_argument_group(
            "Authentication",
            description="Basic authentication will be selected if a username and password is provided. Bearer token authentication will be selected in a token is provided.",
        )
        auth_group.add_argument("--username", help="Username for Basic authentication")
        auth_group.add_argument("--password", help="Password for Basic authentication")
        auth_group.add_argument("--token", help="Token for Bearer authentication")

        # Request settings
        req_group = self.parser.add_argument_group("Request Configuration")
        req_group.add_argument(
            "--no-follow-redirects",
            action="store_true",
            help="Don't follow redirects",
        )
        req_group.add_argument(
            "--sleep",
            type=float,
            default=0.5,
            help="Time to wait between requests in seconds",
        )
        req_group.add_argument(
            "--timeout", type=int, default=5, help="Request timeout in seconds"
        )
        req_group.add_argument(
            "--no-verify-ssl",
            "-k",
            action="store_true",
            help="Disable SSL certificate verification",
        )
        req_group.add_argument(
            "--json",
            action="store_true",
            default=True,
            help="Send request body as JSON",
        )
        req_group.add_argument(
            "--form",
            action="store_false",
            dest="json",
            help="Send request body as form data",
        )
        req_group.add_argument(
            "--user-agent",
            default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            help="User-Agent header",
        )
        req_group.add_argument(
            "--accept", default="application/json", help="Accept header"
        )
        req_group.add_argument(
            "-H", "--header", action="append", help="Additional headers (Key: Value)"
        )

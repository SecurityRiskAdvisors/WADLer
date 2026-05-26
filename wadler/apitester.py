# 3rd party & native imports
import json
from dataclasses import dataclass
import requests
from logging import Logger
from typing import List, Dict, Any
from urllib import (
    parse,
)  # needed to resolve odd urllib behavior - perhaps due to lazy loading?


@dataclass
class APITester:
    """Makes test requests to API endpoints discovered in WADL."""

    args: dict
    logger: Logger
    session: requests.Session

    def _generate_test_value(self, param_type: str, param_name: str | None = "value"):
        """Returns a reasonable test value based on the parameter type."""
        param_type = param_type.lower()

        if param_type in ("int", "integer"):
            return 123

        if param_type in ("float", "double", "number"):
            return 12.34

        if param_type in ("bool", "boolean"):
            return True

        if param_type in ("json", "object", "dict"):
            return {"example": "value"}

        if param_type in ("list", "array"):
            return ["item1", "item2"]

        # Default fallback: string
        return f"test_{param_name}"

    def test_endpoint(
        self, base_url: str, endpoint: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Tests all methods of an endpoint.

        Args:
            base_url: Base URL for the API
            endpoint: Endpoint information including path and methods

        Returns:
            List of test results for each method
        """
        path = endpoint["path"]

        # Properly join the base URL and endpoint path
        if not base_url.endswith("/"):
            base_url += "/"
        if path.startswith("/"):
            path = path[1:]
        full_url = base_url + path

        results = []

        # Skip if endpoint filter is set and doesn't match
        if self.args.endpoint and not any(
            ep in path for ep in self.args.endpoint.split(",")
        ):
            self.logger.debug(f"Skipping endpoint {path} (doesn't match filter)")
            return results

        for method_info in endpoint["methods"]:
            method = method_info["method"]

            # Skip if method filter is set and doesn't match
            if self.args.method and method not in self.args.method.split(","):
                self.logger.debug(
                    f"Skipping {method} {path} (doesn't match method filter)"
                )
                continue

            self.logger.info(f"[bold blue]Testing[/bold blue] {method} {full_url}")

            # Prepare parameters
            params = {}
            data = {}
            headers = {}
            missing_required_params = []

            for param in method_info["params"]:

                param_name = param["name"]
                param_style = param["style"]
                param_required = param["required"]

                # Use default value if available, otherwise use a placeholder
                if param["default"] is not None:
                    param_value = param["default"]
                else:
                    param_value = self._generate_test_value(
                        param_type=param["type"], param_name=param_name
                    )

                if param_style == "query":
                    params[param_name] = param_value
                elif param_style == "header":
                    headers[param_name] = param_value
                elif param_style in ("template", "matrix"):
                    # Template params are part of the URL path
                    template_key = f"{{{param_name}}}"
                    if template_key in full_url:
                        full_url = full_url.replace(
                            template_key, parse.quote(str(param_value))
                        )
                    elif param_required:
                        missing_required_params.append(param_name)
                else:
                    # Assume form or plain params go in the request body
                    data[param_name] = param_value

            if missing_required_params:
                error_msg = f"Missing required template parameters: {', '.join(missing_required_params)}"
                self.logger.error(error_msg)
                results.append({"method": method, "url": full_url, "error": error_msg})
                continue

            try:
                response = self._make_request(method, full_url, params, data, headers)

                # Log the result
                status = response.status_code
                if status < 400:
                    status_color = "green"
                elif status < 500:
                    status_color = "yellow"
                else:
                    status_color = "red"

                self.logger.info(
                    f"Response: [[{status_color}]{status}[/{status_color}]] {response.reason}"
                )

                # Store the result
                result = {
                    "method": method,
                    "url": full_url,
                    "status_code": status,
                    "reason": response.reason,
                    "response_time": response.elapsed.total_seconds(),
                    "response_size": len(response.content),
                }

                # Try to parse response content if it's JSON
                if "application/json" in response.headers.get("Content-Type", ""):
                    try:
                        result["response_body"] = response.json()
                    except json.JSONDecodeError:
                        result["response_body"] = (
                            response.text[:200] + "..."
                            if len(response.text) > 200
                            else response.text
                        )
                else:
                    result["response_body"] = (
                        response.text[:200] + "..."
                        if len(response.text) > 200
                        else response.text
                    )

                results.append(result)

            except Exception:
                self.logger.error(f"Request failed for url: {full_url}")
                results.append({"method": method, "url": full_url, "error": str(e)})

        return results

    def _make_request(
        self, method: str, url: str, params: Dict, data: Dict, headers: Dict
    ) -> requests.Response:
        """Makes an HTTP request with the given parameters."""
        kwargs = {
            "params": params,
            "headers": headers,
            "timeout": self.args.timeout,
            "verify": not self.args.no_verify_ssl,
            "allow_redirects": not self.args.no_follow_redirects,
        }

        # Log request details at debug level
        self.logger.debug(f"Request URL: {url}")
        self.logger.debug(f"Request method: {method}")
        self.logger.debug(f"Request params: {params}")
        self.logger.debug(f"Request headers: {headers}")

        if data and method not in ["GET", "HEAD"]:
            # Check if we should send JSON
            if self.args.json:
                kwargs["json"] = data
                self.logger.debug(f"Request JSON body: {data}")
            else:
                kwargs["data"] = data
                self.logger.debug(f"Request form data: {data}")

        response = self.session.request(method, url, **kwargs)
        return response

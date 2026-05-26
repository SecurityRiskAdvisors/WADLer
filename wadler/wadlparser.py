# 3rd party & native imports
from xml.etree.ElementTree import Element
from dataclasses import dataclass
import requests
from logging import Logger
from lxml import etree
from typing import List, Dict, Any

# internal imports


@dataclass
class WADLParser:
    """Parser for WADL API description files."""

    NAMESPACES = {
        "wadl": "http://wadl.dev.java.net/2009/02",
        "xs": "http://www.w3.org/2001/XMLSchema",
    }

    wadl_source: str
    session: requests.Session
    verify_ssl: bool
    logger: Logger
    root: Element | None = None
    base_url: str | None = None

    def parse(self) -> None:
        """Parses the WADL file and extract the base URL."""
        self.logger.info(f"Parsing WADL from: {self.wadl_source}")

        try:
            if self.wadl_source.startswith(("http://", "https://")):
                # Use the provided session and SSL verification setting
                response = self.session.get(self.wadl_source, verify=self.verify_ssl)
                self.logger.debug(f"WADL fetch status: {response.status_code}")
                response.raise_for_status()
                self.root = etree.fromstring(response.content)
            else:
                self.root = etree.parse(self.wadl_source).getroot()

            # Extract base URL from resources element
            resources_elem = self.root.xpath(
                "//wadl:resources", namespaces=self.NAMESPACES
            )
            if resources_elem:
                self.base_url = resources_elem[0].get("base")
                self.logger.info(f"Base URL: {self.base_url}")
            else:
                self.logger.warning("No base URL found in WADL")
        except Exception:
            self.logger.error(f"Failed to parse WADL: {self.wadl_source}")
            raise

    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        Extracts all endpoints from the WADL document.

        Returns:
            List of endpoint dictionaries containing path, methods, and parameters
        """
        if self.root is None:
            self.parse()

        endpoints = []

        # Find all resource elements
        resources = self.root.xpath(
            "//wadl:resources/wadl:resource", namespaces=self.NAMESPACES
        )

        for resource in resources:
            self._process_resource(resource, "", endpoints)

        return endpoints

    def _process_resource(
        self, resource_elem, parent_path: str, endpoints: List[Dict[str, Any]]
    ) -> None:
        """
        Processes a resource element and its children recursively.

        Args:
            resource_elem: The resource XML element
            parent_path: Path of the parent resource
            endpoints: List to populate with endpoint information
        """
        # Get path from this resource
        path = resource_elem.get("path", "")
        full_path = f"{parent_path}/{path}".replace("//", "/")

        # Process methods in this resource
        methods = resource_elem.xpath("./wadl:method", namespaces=self.NAMESPACES)

        if methods:
            endpoint_info = {"path": full_path, "methods": []}

            for method in methods:
                http_method = method.get("name", "GET").upper()

                # Extract parameters
                params = []
                param_elements = resource_elem.xpath(
                    "./wadl:param", namespaces=self.NAMESPACES
                )
                param_elements.extend(
                    method.xpath(".//wadl:param", namespaces=self.NAMESPACES)
                )

                for param in param_elements:
                    param_info = {
                        "name": param.get("name", ""),
                        "type": param.get("type", "xs:string"),
                        "style": param.get("style", "query"),
                        "required": param.get("required", "false").lower() == "true",
                        "default": param.get("default", None),
                    }
                    params.append(param_info)

                endpoint_info["methods"].append(
                    {
                        "method": http_method,
                        "params": params,
                        "id": method.get("id", ""),
                        "description": self._get_doc(method),
                    }
                )

            endpoints.append(endpoint_info)

        # Process child resources
        child_resources = resource_elem.xpath(
            "./wadl:resource", namespaces=self.NAMESPACES
        )
        for child in child_resources:
            self._process_resource(child, full_path, endpoints)

    def _get_doc(self, element) -> str:
        """Extracts documentation from an element."""
        doc_elem = element.xpath("./wadl:doc", namespaces=self.NAMESPACES)
        if doc_elem and doc_elem[0].text:
            return doc_elem[0].text.strip()
        return ""

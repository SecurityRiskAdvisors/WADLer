from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from fastapi.responses import Response
import inspect
import xml.etree.ElementTree as ET

app = FastAPI()

# -----------------------------
# Dummy endpoints
# -----------------------------


@app.get("/users")
def get_users(role: str | None = None):
    return {"message": "Fetched users", "filter": role}


@app.post("/users")
def create_user(payload: dict):
    return {"message": "User created", "user": payload}


@app.put("/users/{id}")
def update_user(id: int, payload: dict):
    return {"message": "User updated", "id": id, "updated": payload}


@app.delete("/user")
def delete_user(id: int):
    return {"message": "User deleted", "id": id}


# -----------------------------
# Dynamic WADL generation (run once)
# -----------------------------

WADL_XML = None


def _get_type_name(field) -> str:
    # Try common attributes across Pydantic/FastAPI versions
    t = getattr(field, "annotation", None) or getattr(field, "outer_type_", None)
    if t is None:
        return "string"

    # Unwrap typing.Optional, typing.Annotated, etc.
    origin = getattr(t, "__origin__", None)
    if origin is not None and hasattr(origin, "__name__"):
        return origin.__name__

    if hasattr(t, "__name__"):
        return t.__name__

    return str(t)


def generate_wadl(base_url: str) -> bytes:
    wadl = ET.Element("application", xmlns="http://wadl.dev.java.net/2009/02")
    resources = ET.SubElement(wadl, "resources", base=base_url)

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        path = route.path.lstrip("/")
        resource = ET.SubElement(resources, "resource", path=path)

        for method in route.methods:
            if method in ("HEAD", "OPTIONS"):
                continue

            m = ET.SubElement(resource, "method", name=method)
            req = ET.SubElement(m, "request")

            # -------------------------
            # Query parameters
            # -------------------------
            for qp in route.dependant.query_params:
                type_name = _get_type_name(qp)
                required = str(getattr(qp, "required", True)).lower()

                ET.SubElement(
                    req,
                    "param",
                    name=qp.name,
                    style="query",
                    type=type_name,
                    required=required,
                )

            # -------------------------
            # Path parameters
            # -------------------------
            for pp in route.dependant.path_params:
                type_name = _get_type_name(pp)

                ET.SubElement(
                    req,
                    "param",
                    name=pp.name,
                    style="template",
                    type=type_name,
                    required="true",
                )

            # -------------------------
            # Body parameter (if any)
            # -------------------------
            body_field = getattr(route, "body_field", None)
            if body_field is not None:
                type_name = _get_type_name(body_field)

                ET.SubElement(
                    req,
                    "param",
                    name="body",
                    style="body",
                    type=type_name,
                    required="true",
                )

            # Representations
            ET.SubElement(req, "representation", mediaType="application/json")

            resp = ET.SubElement(m, "response", status="200")
            ET.SubElement(resp, "representation", mediaType="application/json")

    return ET.tostring(wadl, encoding="utf-8")


@app.on_event("startup")
async def build_wadl_once():
    global WADL_XML
    # Base URL is static here; you can make it configurable
    WADL_XML = generate_wadl("http://localhost:8000/")


# -----------------------------
# Serve the pre-generated WADL
# -----------------------------


@app.get("/application.wadl")
def serve_wadl():
    return Response(content=WADL_XML, media_type="application/xml")

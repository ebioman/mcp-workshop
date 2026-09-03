#!/usr/bin/env python3

import sys
from json import load
from pathlib import Path
from subprocess import run
from typing import Annotated
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from mcp.server import MCPServer
from pydantic import Field


CELL_MODEL_PASSPORTS_API_BASE = "https://api.cellmodelpassports.sanger.ac.uk"

mcp = MCPServer("depmap-mcp")


@mcp.tool(title="DepMap: id of gene")
def get_gene_id(
    gene_name: Annotated[
        str,
        Field(
            description=(
                "Required. gene symbol to search for. Example: KRAS"
            )
        ),
    ]
) -> dict:
    """
    Identifies the corresponding ID (e.g. SIDG...) of genes (e.g. TP53) in the DepMap catalog
    """
    print(
        "Tool searches ID for the following gene: "
        f"query={gene_name}",
        file=sys.stderr,
    )

    # Sanger API uses JSON API standard filtering
    filter_string = f'[{{"name":"symbol","op":"eq","val":"{gene_name}"}}]'
    parameters = urlencode({"filter": filter_string})
    url = f"{CELL_MODEL_PASSPORTS_API_BASE}/genes?{parameters}"

    try:
        with urlopen(url, timeout=20) as response:
            data = load(response)
            if not data.get("data"):
                return {"error": f"No gene found matching symbol '{gene_name}'."}
            
            # Return just the ID and symbol to save LLM context
            return {
                "symbol": gene_name,
                "gene_id": data["data"][0]["id"]
            }
    except HTTPError as error:
        return {"error": f"HTTP {error.code}"}
    except URLError as error:
        return {"error": str(error)}



@mcp.tool(title="DepMap: models with mutations in gene")
def get_mutated_celllines(
    gene_id: Annotated[
        str,
        Field(
            description=(
                "Required. Sanger gene ID to search for . Example: SIDG13960."
            )
        ),
    ]
) -> dict:
    """
    Identifies the cell-line models in the the DepMap catalog which carry mutations in the provided id.
    """
    print(
        "Tool searches models for the following gene ID: "
        f"query={gene_id}",
        file=sys.stderr,
    )
    #currently only snp here
    url = f"{CELL_MODEL_PASSPORTS_API_BASE}/models/by_snp/{gene_id}"

    try:
        with urlopen(url, timeout=20) as response:
            data = load(response)
            if not data.get("data"):
                return {"error": f"No model found matching mutation in '{gene_id}'."}
            # Return just the ID and symbol to save LLM context
            extract =[
                {
                    "model_id" : item["id"],
                    "names": item.get("attributes", {}).get("names"), 
                    "model_type": item.get("attributes", {}).get("model_type"),
                }
                for item in data.get("data", [])
            ]
            

            return {
                "gene_id_queried": gene_id,
                "mutation_type": "snp",
                "total_found": len(extract),
                "models": extract
            }
        
    except HTTPError as error:
        return {"error": f"HTTP {error.code}"}
    except URLError as error:
        return {"error": str(error)}




if __name__ == "__main__":

    try:
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000,
            stateless_http=True,
        )
    except KeyboardInterrupt:
        pass

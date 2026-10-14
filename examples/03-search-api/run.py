"""Example 03: STAC search with stac-fastapi."""
# This example shows the server-side setup.
# Run with: uvicorn server:app --reload

from pystac import Catalog
from stac_fastapi.api.app import StacApi
from stac_fastapi.extensions.core import TransactionExtension

# Create a minimal catalog
catalog = Catalog(id="demo", description="Demo API")

# Configure API
api = StacApi(
    title="ZQM STAC API",
    description="Demo STAC API for geospatial search",
    catalog=catalog,
    extensions=[TransactionExtension()],
)

# Get the FastAPI app
app = api.app
print("STAC API configured")
print("Run with: uvicorn server:app --reload")
print("Then query: http://localhost:8000/search")

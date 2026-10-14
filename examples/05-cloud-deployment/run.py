"""Example 05: Deploy STAC catalog to S3."""

from pystac import Catalog

# Create catalog
catalog = Catalog(id="zqm-cloud-catalog", description="Cloud-hosted STAC catalog")

# Save locally first
catalog.normalize_and_save("output/cloud_catalog")

# Upload to S3 (requires AWS credentials)
# s3 = boto3.client("s3")
# bucket = "zqm-stac-catalogs"
# for json_file in Path("output/cloud_catalog").rglob("*.json"):
#     s3.upload_file(str(json_file), bucket, str(json_file.relative_to("output/cloud_catalog")))

print("Catalog prepared for cloud deployment")
print("To deploy: uncomment S3 upload code and set bucket name")
print("Catalog path: output/cloud_catalog")

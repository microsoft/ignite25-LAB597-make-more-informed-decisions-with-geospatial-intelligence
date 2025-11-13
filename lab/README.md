# Lab: School Greening Analysis with Microsoft Planetary Computer Pro

## Overview
This lab demonstrates how to use Microsoft Planetary Computer Pro and Azure Databricks to analyze urban heat islands around school campuses in Phoenix, Arizona. You'll work with satellite imagery and geospatial data to assess vegetation coverage (NDVI) and land surface temperature (LST) for schools in the Phoenix area.

The notebook walks through accessing geospatial data from a private GeoCatalog instance, processing STAC (SpatioTemporal Asset Catalog) collections, and visualizing environmental conditions around educational facilities.

**Note:** All required infrastructure (Azure Databricks workspace, GeoCatalog instance, authentication credentials) is pre-configured in the lab environment.

## Prerequisites

### Lab Environment
- **Azure Databricks Workspace**: The notebook must be run in Azure Databricks as it requires Spark context (`sc`) for distributed processing
- **GeoCatalog Access**: Private GeoCatalog instance at `https://lab597geocatalog.czeteqbrbtb7gzcz.northcentralus.geocatalog.spatio.azure.com/`
- **Authentication**: Azure Managed Identity with **GeoCatalog Admin** RBAC role assigned
- **Python Environment**: Python 3.x with Databricks Runtime

### Required Python Libraries
The notebook uses the following geospatial and data science libraries:
- `geopandas` - Geospatial data manipulation
- `rasterio` & `rioxarray` - Raster data I/O and processing
- `xarray` - Multi-dimensional array operations
- `pystac` & `pystac-client` - STAC catalog querying
- `planetary_computer` - Microsoft Planetary Computer SDK
- `matplotlib` - Visualization
- `contextily` - Basemap tiles for maps
- `shapely` - Geometric operations
- `pyproj` - Coordinate reference system transformations

## Data Sources

### GeoCatalog STAC Collections
The lab uses two primary STAC collections from the private GeoCatalog instance:

#### 1. NAIP (National Agriculture Imagery Program)
- **Collection ID**: `naip`
- **Purpose**: High-resolution aerial imagery with 4 bands including Near-Infrared (NIR)
- **Use Case**: Calculate NDVI (Normalized Difference Vegetation Index) to assess vegetation health and coverage
- **Resolution**: 0.6-1.0 meter/pixel
- **Bands Used**: Red and NIR for NDVI calculation

#### 2. Landsat Collection 2 Level 2
- **Collection ID**: `landsat-c2-l2`
- **Purpose**: Multispectral satellite imagery including thermal bands
- **Use Case**: Calculate Land Surface Temperature (LST) to measure urban heat patterns
- **Resolution**: 30 meters/pixel (multispectral), 100 meters/pixel (thermal)
- **Bands Used**: Thermal bands (B10) and quality assessment (QA) bands

### School Locations Dataset
- **File**: `phoenix_schools.geojson`
- **Format**: GeoJSON FeatureCollection
- **CRS**: WGS84 (EPSG:4326)
- **Content**: Polygon geometries representing school campuses in the Phoenix metropolitan area
- **Attributes**: School names, addresses, operators, and other OpenStreetMap properties
- **Source**: OpenStreetMap data for Phoenix area schools

## Authentication Architecture

The notebook uses Azure Managed Identity for secure, credential-free authentication:
1. **ManagedIdentityCredential**: Azure identity credential provider
2. **Token Broadcasting**: Authentication token is broadcast via Spark (`sc.broadcast`) for distributed access
3. **SAS Token Generation**: Collection-specific Shared Access Signature tokens are generated for NAIP and Landsat collections
4. **RBAC Role**: GeoCatalog Admin role assignment enables full access to catalog resources

## Lab Workflow

### 1. Environment Setup
- Import required libraries
- Configure authentication with Azure Managed Identity
- Connect to private GeoCatalog instance
- Generate SAS tokens for STAC collections

### 2. Data Loading
- Load `phoenix_schools.geojson` with school geometries
- Preview school locations and attributes

### 3. Geospatial Analysis
- Query NAIP collection for recent aerial imagery
- Query Landsat collection for thermal data
- Calculate NDVI from NAIP imagery (vegetation index)
- Calculate LST from Landsat thermal bands (land surface temperature)
- Apply quality masks to filter cloud-contaminated pixels

### 4. Visualization
- Display school footprints with NDVI overlay
- Generate maps showing vegetation coverage
- Visualize land surface temperature patterns
- Compare results across multiple school campuses

## Key Functions

- `token_auth()`: Manages Azure Managed Identity authentication
- `get_collection_sas_token()`: Retrieves SAS tokens for STAC collections
- `expand_bounds()`: Buffers geometries for area-of-interest queries
- `most_recent_openpc_item()`: Finds most recent STAC items for a collection
- `display_school_footprint()`: Visualizes school geometry with satellite data
- `display_school_results()`: Generates comparative analysis visualizations

## Additional Resources

- [Microsoft Planetary Computer Pro Documentation](https://planetarycomputer.microsoft.com/)
- [STAC Specification](https://stacspec.org/)
- [GeoCatalog Documentation](https://aka.ms/azuremapsgeocatalog)
- [Azure Databricks Documentation](https://learn.microsoft.com/azure/databricks/)
- [NAIP Imagery Information](https://www.fsa.usda.gov/programs-and-services/aerial-photography/imagery-programs/naip-imagery/)
- [Landsat Collection 2 Documentation](https://www.usgs.gov/landsat-missions/landsat-collection-2)

---

## Building the Lab Environment

If you need to recreate this lab environment from scratch, the following resources are available in the [`setup/`](./setup/) folder:

### Infrastructure Components

The lab environment consists of the following Azure resources:

1. **Azure Databricks Workspace** (Premium tier with Unity Catalog)
2. **GeoCatalog Instance** (Pre-configured with NAIP and Landsat collections)
3. **Managed Identity** (For authentication between Databricks and GeoCatalog)
4. **RBAC Role Assignment** (GeoCatalog Administrator role)

### Deployment Templates

#### ARM Template
- **File**: [`databricks_cloud_resource_template.json`](./setup/databricks_cloud_resource_template.json)
- **Purpose**: Deploys Azure Databricks workspace with managed identity and assigns GeoCatalog Admin permissions
- **Key Parameters**:
  - `workspaceName`: Name of the Databricks workspace (default: `Ignite25Lab597`)
  - `managedResourceGroup`: Name for Databricks-managed resource group
  - `geoCatalogSubscriptionId`: Subscription ID where GeoCatalog is deployed
  - `geoCatalogResourceGroup`: Resource group containing GeoCatalog
  - `geoCatalogName`: Name of the GeoCatalog instance (default: `Lab597GeoCatalog`)
  - `location`: Azure region (default: `northcentralus`)

#### PowerShell Scripts

**User Permission Assignment**: [`Assign-UserPermissions.ps1`](./setup/Assign-UserPermissions.ps1)
- Assigns GeoCatalog Administrator role to lab users
- Executed as a post-build step in the lab environment

**Databricks Configuration**: [`Configure-Databricks.ps1`](./setup/Configure-Databricks.ps1)
- Installs Databricks CLI
- Creates and configures compute cluster with required specifications:
  - Spark version: 17.2.x-scala2.13
  - Node type: Standard_D4ads_v5
  - Autoscaling: 2-8 workers
  - Photon runtime engine enabled
  - Spot instances with fallback
- Installs required Python libraries:
  - `httpx`, `azure-identity`, `aiohttp`
  - `geopandas`, `contextily`, `shapely`, `folium`
  - `planetary-computer`, `pystac-client`, `rioxarray`
  - `tqdm`
- Downloads and imports lab resources:
  - `phoenix_schools.geojson`
  - `school-greening.ipynb`

### Deployment Steps

1. **Deploy GeoCatalog** (prerequisite):
   - Create a GeoCatalog instance in Azure
   - Ingest NAIP and Landsat-C2-L2 STAC collections
   - Note the subscription ID, resource group, and GeoCatalog name

2. **Deploy Databricks Workspace**:
   ```bash
   az deployment group create \
     --resource-group <your-resource-group> \
     --template-file setup/databricks_cloud_resource_template.json \
     --parameters workspaceName=<workspace-name> \
                  geoCatalogSubscriptionId=<geocatalog-sub-id> \
                  geoCatalogResourceGroup=<geocatalog-rg> \
                  geoCatalogName=<geocatalog-name>
   ```

3. **Assign User Permissions**:
   - Run [`Assign-UserPermissions.ps1`](./setup/Assign-UserPermissions.ps1) to grant users GeoCatalog Administrator access
   - Modify the script to include appropriate user principal names

4. **Configure Databricks**:
   - Run [`Configure-Databricks.ps1`](./setup/Configure-Databricks.ps1) to set up compute cluster and install libraries
   - Update the script with your workspace URL and resource group name

5. **Verify Deployment**:
   - Log into Databricks workspace
   - Confirm cluster is running
   - Open `school-greening.ipynb` notebook
   - Verify authentication to GeoCatalog succeeds

### Environment Variables

The following variables should be configured:
- `MPC_APP_ID`: Azure AD Application ID (for Managed Identity)
- Databricks workspace URL
- GeoCatalog endpoint URL

### Notes

- The managed identity created by Databricks must have the **GeoCatalog Administrator** role on the GeoCatalog instance
- Cluster configuration includes `OGR_GEOMETRY_ACCEPT_UNCLOSED_RING=YES` environment variable for geometry handling
- Library versions are pinned for consistency across lab environments
- The setup is designed for single-user Databricks clusters with legacy authentication mode

For detailed setup instructions and troubleshooting, refer to the [`setup/README.md`](./setup/README.md) file.

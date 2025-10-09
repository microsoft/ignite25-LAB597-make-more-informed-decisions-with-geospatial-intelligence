$ResourceGroupName = "Ignite25Lab597"

# Get the most recent deployment and extract workspace URL
$deployment = Get-AzResourceGroupDeployment -ResourceGroupName $ResourceGroupName | Select-Object -First 1
$workspaceUrl = $deployment.Outputs.databricksWorkspaceUrl.Value

Set-LabVariable -Name databricksWorkspaceUrl -Value "https://$workspaceUrl"

# Install Databricks CLI
$downloadUrl = "https://github.com/databricks/cli/releases/download/v0.271.0/databricks_cli_0.271.0_linux_amd64.zip"
Invoke-WebRequest -Uri $downloadUrl -OutFile databricks_cli.zip
Expand-Archive -Path databricks_cli.zip -DestinationPath ./cli -Force

# Get Azure AD token for Databricks
$tokenResponse = Get-AzAccessToken -ResourceUrl "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"

# Configure Databricks CLI
$env:DATABRICKS_HOST = "https://$workspaceUrl"
$env:DATABRICKS_TOKEN = $tokenResponse.Token

# Cluster configuration
$clusterConfig = @{
    cluster_name = "Lab Cluster"
    data_security_mode = "LEGACY_SINGLE_USER_STANDARD"
    single_user_name = "@lab.CloudPortalCredential(User1).Username"
    kind = "CLASSIC_PREVIEW"
    azure_attributes = @{
        availability = "SPOT_WITH_FALLBACK_AZURE"
    }
    runtime_engine = "PHOTON"
    spark_version = "17.2.x-scala2.13"
    node_type_id = "Standard_D4ads_v5"
    spark_env_vars = @{
        OGR_GEOMETRY_ACCEPT_UNCLOSED_RING = "YES"
    }
    autotermination_minutes = 240
    is_single_node = $false
    autoscale = @{
        min_workers = 2
        max_workers = 8
    }
} | ConvertTo-Json -Depth 10

# Create cluster
$cluster = ./cli/databricks clusters create --no-wait --json $clusterConfig | ConvertFrom-Json

# Install libraries
$libraries = @{
    cluster_id = $cluster.cluster_id
    libraries = @(
        @{pypi = @{package = "httpx==0.28.1"}},
        @{pypi = @{package = "azure-identity==1.25.0"}},
        @{pypi = @{package = "aiohttp==3.12.15"}},
        @{pypi = @{package = "geopandas==1.1.1"}},
        @{pypi = @{package = "contextily==1.6.2"}},
        @{pypi = @{package = "planetary-computer==1.0.0"}},
        @{pypi = @{package = "rioxarray==0.19.0"}},
        @{pypi = @{package = "pystac-client==0.9.0"}},
        @{pypi = @{package = "shapely==2.1.2"}},
        @{pypi = @{package = "folium==0.20.0"}},
        @{pypi = @{package = "tqdm==4.67.1"}}
    )
} | ConvertTo-Json -Depth 10
./cli/databricks libraries install --json $libraries

return $true

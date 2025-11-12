@lab.Title

## Welcome to Your Lab Environment

To begin, sign in to the virtual machine using the following credentials: +++@lab.VirtualMachine(Win11-Pro-Base).Password+++

**Note:** Text formatted as an +++example+++ represents type text. Clicking on this text will automatically insert it to prevent any typing errors.

After logging in, if you see:
* "You're almost done setting up your PC," hit the **Remind me in 3 days** button.
* "Protect your files and memories by backing up your PC", hit the **Opt-out** and **Skip** selections

===

## About this Lab

This lab walks you through using the Azure Cloud and the Microsoft Planetary Computer to analyze facilities to improve efficiencies in their operations.

The primary analysis environment for this scenario is [Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/introduction/), a cloud-native platform for conducting analytics. 

To access the Azure portal, open the **Microsoft Edge** browser.

!IMAGE[Screenshot 2025-10-09 155523.png](instructions310546/Screenshot 2025-10-09 155523.png)

Then, navigate to the Azure portal at `https://portal.azure.com/` once the virtual machine is booted up. 

!IMAGE[Screenshot 2025-10-09 155652.png](instructions310546/Screenshot 2025-10-09 155652.png)

===
## Signing in to the Azure portal

To sign in to the Azure portal, use the **Username** located in the **Resources** tab of the Lab Environment. 

You will then be prompted to enter a Temporary Access Password. In the **Resources** tab, use the **TAP** code that is provided and select the **Sign In** button. 

===

## Locating the GeoCatalog resource

Microsoft Planetary Computer Pro resources are known as **GeoCatalogs** and are available to be created through the Azure portal. 

A GeoCatalog has already been created for this lab.

To find existing **GeoCatalogs** search in the top bar of the Azure portal for **GeoCatalogs**:
!IMAGE[x3rk7dw2.jpg](instructions310546/x3rk7dw2.jpg)

Select **GeoCatalogs** from the Services dropdown. 

===
## GeoCatalog Resource Viewer

This view allows you to see existing GeoCatalog resources and also create new GeoCatalog resources. 

For this exercise, we will be using the **Lab597GeoCatalog** resource. 

Organizations typically create GeoCatalogs centrally to ingest, manage, and share geospatial data.

Select the **Lab597GeoCatalog** resource to open the management portal: 
!IMAGE[hv9flckn.jpg](instructions310546/hv9flckn.jpg)

This is a shared resource for all students of this lab. Please do not delete or alter any settings with this resource. 

===
### GeoCatalog Management View

In this view, you can modify the settings associated with this resource. 

For the purposes of this lab, access controls have already been established and no further configuration is required. 

To browse the content inside a GeoCatalog, click the **GeoCatalog URI** to enter the GeoCatalog web interface:
 !IMAGE[x7xq27z8.jpg](instructions310546/x7xq27z8.jpg)

You can also enter this link into the portal to get to this view:
`https://lab597geocatalog.czeteqbrbtb7gzcz.northcentralus.geocatalog.spatio.azure.com`

This is the GeoCatalog endpoint, which will be used to connect to both the web view and all API services for adding or accessing data from inside a GeoCatalog.  

===
## Welcome to your Planetary Computer Pro!

For this scenario, you are a planner with the City of Phoenix, Arizona. You are interested in understanding urban heat islands and their impacts to your community's schools. Schools that are too hot make it challenging for students to enjoy the outdoors and safely participate in sports. As we go through this exercise, you'll see on any given day, there are significant temperature differences for individual schools in your community. Planners can then use this information to help make changes to the landscaping and layout of the school to improve shade and greenspace to help reduce the urban heat island effect. 

Microsoft Planetary Computer Pro is a cloud-native platform-as-a-service product for managing the lifecycle with geospatial data. 

It allows an enterprise to centralize all their geospatial holdings for use with a variety of applications and workflows. It fills a need to make this data searchable, queryable and viewable for applications. This is not possible from any pure storage or database service. 

In this view, you are seeing the geospatial data the City of Phoenix has collected. 

This catalog contains multiple aerial surveys over the City of Phoenix, and weather data about the City of Phoenix. All data is organized using an open standard known as the Spatio Temporal Asset Catalog or [STAC](https://stacspec.org/en/). STAC metadata enables consistent spatial and temporal search across diverse datasets.

Let's explore some of this aerial data: select **City of Phoenix School Imagery**:
!IMAGE[18dzww5z.jpg](instructions310546/18dzww5z.jpg)

===

## Collection View

Data inside Planetary Computer Pro is organized in groupings called [collections](https://learn.microsoft.com/en-us/azure/planetary-computer/stac-overview#stac-collections). 

In this view, you can see the individual pieces of data, or [STAC Items](https://learn.microsoft.com/en-us/azure/planetary-computer/stac-overview#stac-items). 

Let's see what data has been loaded into this collection by selecting the **STAC Items** tab:
!IMAGE[rx958a95.jpg](instructions310546/rx958a95.jpg)

Here, you can see a complete list of the schools in the Phoenix area that have been surveyed.

Select a name of any school to see a preview of the data, and see the associated metadata: 
!IMAGE[r8nl0ny7.jpg](instructions310546/r8nl0ny7.jpg)

Metadata is important information associated with the collected geospatial data. Once this data is loaded into a GeoCatalog, all metadata becomes searchable across all datasets. 

The STAC standard enforces specific metadata fields such as the spatial extent (latitude/longitude), which means you can always correlate different datasets. This will be important in the analysis part of the lab when we begin to combine different datasets. 

Also notice the **GSD**, this is the ground sample distance for this particular image. A GSD of .1016 means each pixel in this image is equivalent to 10 centimeters on the ground. This is extremely high-resolution data, which is perfect for urban planning applications. 

In this view, if you want to add additional data to this collection, you would hit the Add Item button. For the purposes of this lab, adding additional data is not required. 

Next, let's return to the **Overview** to start exploring the data more:
!IMAGE[swgbo7a0.jpg](instructions310546/swgbo7a0.jpg)  

===

## Exploring Data

Next, let's visualize this data on a map, select the **Launch in Explorer** button to view this data interactively
!IMAGE[euiebqci.jpg](instructions310546/euiebqci.jpg)

In this view, you can see all the schools in the area precisely layered on a basemap covering the City of Phoenix-
!IMAGE[qcl7j8x0.jpg](instructions310546/qcl7j8x0.jpg)

The Explorer allows you to quickly test and verify your data is in your GeoCatalog and view it in its spatial context. Using Explorer first helps confirm spatial coverage before programmatic access in Databricks.

Every view you see in Explorer can be recreated using the APIs and can then be embedded in applications. This makes it super simple for developers to use this data for innovative applications. For example, the left panel is showing what a search of "All the school data over Phoenix" would yield. Select the **Explore results in code** to see how to generate this view.
!IMAGE[ztys05xo.jpg](instructions310546/ztys05xo.jpg)

We'll be using these APIs in Azure Databricks to dynamically call the data stored in GeoCatalog to do our analysis. 

Feel free to explore this view and zoom in and out to check out the various schools. All this data is being dynamically tiled from the Azure cloud. 

When you are finished, **return to the Azure portal** to move to the analysis section of this lab: `https://portal.azure.com/`

===

## Loading the Azure Databricks Workspace

Once back in the Azure portal (`https://portal.azure.com/`), in the top navigation bar for the Azure portal, search for **"Azure Databricks"**

!IMAGE[Azure-Databricks.png](instructions310546/Azure-Databricks.png)

After searching for "Azure Databricks", you will see an Azure Databricks workspace that has already been created for you called **Ignite25Lab597**

Select **Ignite25Lab597**

!IMAGE[Screenshot 2025-10-09 155100.png](instructions310546/Screenshot 2025-10-09 155100.png)

Once inside the Azure Databricks resource, select the **Launch Workspace** button. 

!IMAGE[Screenshot 2025-10-09 155309.png](instructions310546/Screenshot 2025-10-09 155309.png)

===

## Loading the Azure Databricks Notebook

The lab contents are housed in a notebook which needs to be opened.

Once in the Azure Databricks web interface, on the left-hand side, select the **Workspace** button.
!IMAGE[Screenshot 2025-10-10 091738.png](instructions310546/Screenshot 2025-10-10 091738.png) 

Then, click the **Workplace** folder, and then click the **Shared** subfolder. 
!IMAGE[Screenshot 2025-10-10 091856.png](instructions310546/Screenshot 2025-10-10 091856.png)

Next, click the the **school-greening.ipynb** file to open the notebook.
!IMAGE[Screenshot 2025-10-10 092255.png](instructions310546/Screenshot 2025-10-10 092255.png)

===

## Starting the Notebook

This lab uses an interactive notebook to run code in the Azure Cloud using Azure Databricks. 

Many things have been setup ahead of time to allow students to focus on the new concepts introduced in this lab, and not the details on executing this notebook. Things like provisioning of a compute cluster, permissions and loading of data were executed on the boot up of this lab environment. 

To begin, you first must attach the pre-provisioned compute cluster to the notebook. 

On the top right, select the **Connect** button, and then select **Lab Cluster**.

!IMAGE[Screenshot 2025-10-10 093444.png](instructions310546/Screenshot 2025-10-10 093444.png)

Connection is successful when **Lab Cluster** has a green dot next to it:
!IMAGE[Screenshot 2025-10-10 093653.png](instructions310546/Screenshot 2025-10-10 093653.png)

===

## Running the Notebook

The interactive notebook consists of blocks of text written to explain each step in the analysis process and blocks of code. 

Each block of code can be executed by hitting the **Play button**: !IMAGE[ayesu9le.png](instructions310546/ayesu9le.png)

Wait for the code to complete execution before moving to the next block of code as each step builds on the previous step. 

Step through the content of this notebook, reading the explanations and following along the analysis. 

This notebook processes the data covering the City of Phoenix stored in the GeoCatalog to understand which schools are the hottest in the area. 

===

### Additional Resources

[Documentation for Microsoft Planetary Computer Pro](https://learn.microsoft.com/en-us/azure/planetary-computer/)

Contact the Team: MPCPro@Microsoft.com

**Thank you for participating in this lab!** 
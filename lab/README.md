

These instructions are for participants of the **instructor-led** Workshop "SESSIONNAME" at Microsoft AI Tour 2026.  Register to attend in a city near you at [Microsoft AI Tour](https://aitour.microsoft.com/).

## Lab Overview

This is a notebook based exercise to show students how to use Microsoft Planetary Computer Pro and Databricks to help identify schools in a given city which are hotter than average and could use additional tree cover to help cool their property. 

To do this, we will use several data sources:

* GeoJSON containing list of schools along with latitude and longitude
* Aerial Imagery (NAIP) of the schools, containing both visible and infrared data (help calculate vegitation index)
   
   This data will be stored in a Microsoft Planetary Computer Pro GeoCatalog
* Landsat Surface Temperature Data from the Open Planetary ComputerSamples will be taken over many summers on cloud-free days to understand average temperature for the school. 

This data will be brought together in Databricks to provide a list of schools, their temperature and tree index. This data will then be used to determine which schools need to be greened. 

The exercise will be broken up in several sections-

### Setup:

- Verify Key Resources are PresentGeoCatalog
- Databricks
- Download any necessary material to local machine

### Data Ingestion:

- Load GeoJSON containing locations of POI (Schools)
- Load Corresponding High Resolution Imagery of these locations into GeoCatalog
- Ingest Data
   - Set Render Configuration
   - Preview Data

### Data Processing:

Load Indexed Values from Landsat for Surface Temperature
Calculate NDVI for schools (Tree Index)

### Analysis:

- Stack Rank data based on Hottest Schools with least Tree Index
- Prepare Report: Names of Schools + Imagery, suggestions on how many trees to add


## Pre-Requisites



## Get Started



## Discussions



## Source code

The source code for this session can be found in the [src folder](../src) of this repo.

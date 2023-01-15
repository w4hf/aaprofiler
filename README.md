# AAProfiler

## Description

This python Script scrape AWX or AAP Controller (Tower) API and Generate csv files Reports.
The objects audited are :
- credentials (sensitive data cannot be collected)
- projects
- hosts
- job_templates
- inventories
- inventory sources
- teams
- users
- roles

The results and script log file  will be generated under the folder `results_XXXX` where XXXX is the fqdn of the controller.

All the variables are described below. 

## Requirements

All you need is `python3` (and love)


## Demo

[![asciicast](https://asciinema.org/a/nPl94bUfYLkiAvo22K6dZ0Ws5.svg)](https://asciinema.org/a/nPl94bUfYLkiAvo22K6dZ0Ws5)

PS: In the demo, I removed the roles extraction because it is time-consuming

## Editable Variables

The user should only edit the following variables :

| Variable             | Example Value                                                                 | Description                                                                                                                                                                                                  |
|----------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| controller_fqdn      | www.controller.company.com                                                    | AWX or AAP Controller hostname or IP                                                                                                                                                                         |
| controller_user      | admin                                                                         | AWX or AAP username                                                                                                                                                                                          |
| controller_pass      | *****                                                                         | AWX or AAP password                                                                                                                                                                                          |
| page_size            | 200                                                                           | API page object count limit                                                                                                                                                                                  |
| resources_to_extract | ['credentials', 'projects', 'hosts', 'job_templates', 'roles', 'inventories'] | A list containing the resources to export You can pick and chose which resources to extract. <br/>Restrictions: <br/>- cannot be empty<br/>- resource name should be written exactly as in the default value |


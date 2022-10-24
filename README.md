# AAProfiler

## Description

This python Script scrape AWX or AAP Controller (Tower) API and Generate csv files Reports.
The objects audited are :
- credentials
- projects
- hosts
- job_templates
- roles
- inventories

By default, the results will be generated under the folder `results`. This could be modified by setting the variable `results_dir`

All the variables are described below.

## Requirements

All you need is `python3` (apart from love)

## Editable Variables

The user can edit the following variables :

| Variable             | Default Value                                                                 | Description                                                                                                                                                                                                  |
|----------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| controller_host      | https://localhost                                                             | AWX or AAP Controller hostname or IP                                                                                                                                                                         |
| controller_user      | admin                                                                         | AWX or AAP username                                                                                                                                                                                          |
| controller_pass      | *****                                                                         | AWX or AAP password                                                                                                                                                                                          |
| page_size            | 200                                                                           | API page object count limit                                                                                                                                                                                  |
| results_dir          | results                                                                       | Folder to where export report CSV files                                                                                                                                                                      |
| resources_to_extract | ['credentials', 'projects', 'hosts', 'job_templates', 'roles', 'inventories'] | A list containing the resources to export You can pick and chose which resources to extract. <br/>Restrictions: <br/>- cannot be empty<br/>- resource name should be written exactly as in the default value |


#!/usr/bin/python3
'''
#############################################
#                                           #
#     Project : AAProfiler                  #
#     Author: Hamza Bouabdallah             #
#     Company: RedHat                       #
#     Version: 0.5                          #
#     LinkedIn: www.linkedin.com/in/w4hf    #
#     Github:  @w4hf                        #
#                                           #
#############################################

 This python Script scrape AWX or AAP Controller (Tower) API and Generate csv files Reports.

 The objects extracted are :
 - credentials
 - projects
 - hosts
 - job_templates
 - workflow_job_templates
 - roles
 - inventories
 - inventory sources
 - teams
 - users

 Each object will have its own csv file generated under the 'results_XXX' where XXX is the fqdn of the controller
 Also, a log file named 'extraction.log' is created under the same results directory
'''

import os
import sys
import re
import requests
import socket
from contextlib import closing
from datetime import datetime


requests.packages.urllib3.disable_warnings()

# -------------------------------------------- EDIT ONLY THIS BLOCK !! --------------------------------------------
controller_fqdn = 'controller.example.com'
controller_user = 'admin'
controller_pass = '**********'
controller_port = 443

# Set the API return page object count, should be between 1 and 200.
page_size = 200

# You can extract Everything :
# resources_to_extract = ['host_metrics', 'credentials', 'projects', 'hosts', 'job_templates', 'inventories', 'inventory_sources', 'users', 'teams',  'roles', 'workflow_job_templates']

# OR You can choose a subset to extract :
# resources_to_extract = ['credentials', 'projects', 'job_templates', 'inventories', 'inventory_sources', 'users', 'teams', 'workflow_job_templates']

# Set this to 'True' to fetch Org names instead of Org ID when extracting hosts
# !! Warning setting this to 'True' makes the extraction much slower (depending on how many hosts you have) !!
get_hosts_org_name = False

# -------------------------------------------------------------------------------------------------------------------

# -------------------------------------------- DO NOT EDIT ANYTHING BELOW THIS LINE ! -------------------------------

def extract_inventory_sources(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + ' ...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()
    for source in page_n['results']:
        source_name = source['name']
        source_type = source['source']
        source_inventory = source['summary_fields']['inventory']['name']
        source_organization = source['summary_fields']['organization']['name']

        if source_type == 'scm':
            source_project = source['summary_fields']['source_project']['name']
        else:
            source_project = 'Null'

        source_credentials = list()
        for cred in source['summary_fields']['credentials']:
            source_credentials.append((cred['name'], cred['kind']))

        result = source_organization + ';' + source_name+ ';' + source_type + ';' + source_inventory + ';' + source_project + ';' + str(source_credentials)

        file.write(result + "\n")


def extract_teams(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for team in page_n['results']:
        # Get Hostname
        team_id = team['id']
        team_name = team['name']
        team_org = team['summary_fields']['organization']['name']

        # Get teams users
        team_users = ['']
        r = requests.get(
            controller_host + '/api/v2/teams/' + str(team_id) + '/users?page=1&page_size=' + str(page_size),
            auth=(controller_user, controller_pass), verify=False)
        team_users_page1 = r.json()
        team_users_count = team_users_page1['count']
        team_users_pages_count = team_users_count // page_size + bool(team_users_count % page_size)

        if team_users_count > 0:
            print('+++ Team ' + str(team_id) + ' has ' + str(
                team_users_count) + ' user(s). Extracting it from ' + str(
                team_users_pages_count) + ' page(s).')
            for user_team_page_n in range(1, team_users_pages_count + 1):
                user_team_list_raw = requests.get(
                    controller_host + '/api/v2/teams/' + str(team_id) + '/users?page=' + str(
                        user_team_page_n) + '&page_size=' + str(
                        page_size), auth=(controller_user, controller_pass), verify=False)
                user_team_list = user_team_list_raw.json()
                if user_team_list['results']:
                    for t in user_team_list['results']:
                        team_users.append(t['username'])

        # Removing empty first element
        if len(team_users) > 1 and team_users[0] == '':
            del team_users[0]

        result = str(team_id) + ';' + team_name + ';' + team_org + ';' + str(team_users)

        file.write(result + "\n")


def extract_users(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for user in page_n['results']:
        # Get Hostname
        user_id = user['id']
        username = user['username']

        if user['first_name']:
            user_first_name = user['first_name']
        else:
            user_first_name = 'Null'

        if user['last_name']:
            user_last_name = user['last_name']
        else:
            user_last_name = 'Null'

        # Get ldap_dn
        if user['ldap_dn']:
            user_ldap_dn = user['ldap_dn']
        else:
            user_ldap_dn = 'Null'

        # Get is_superuser
        if user['is_superuser']:
            user_is_superuser = user['is_superuser']
        else:
            user_is_superuser = 'False'

        # Get user teams
        user_teams = ['']
        p = requests.get(
            controller_host + '/api/v2/users/' + str(user_id) + '/teams?page=1&page_size=' + str(page_size),
            auth=(controller_user, controller_pass), verify=False)
        user_teams_page1 = p.json()
        user_teams_count = user_teams_page1['count']
        user_teams_pages_count = user_teams_count // page_size + bool(user_teams_count % page_size)

        if user_teams_count > 0:
            print('+++ User ' + str(user_id) + ' belongs to ' + str(
                user_teams_count) + ' teams(s). Extracting it from ' + str(
                user_teams_pages_count) + ' page(s).')
            for user_team_page_n in range(1, user_teams_pages_count + 1):
                user_team_list_raw = requests.get(
                    controller_host + '/api/v2/users/' + str(user_id) + '/teams?page=' + str(
                        user_team_page_n) + '&page_size=' + str(
                        page_size), auth=(controller_user, controller_pass), verify=False)
                user_team_list = user_team_list_raw.json()
                if user_team_list['results']:
                    for t in user_team_list['results']:
                        user_teams.append(t['name'])

        # Removing empty first element
        if len(user_teams) > 1 and user_teams[0] == '':
            del user_teams[0]

        # Get user Orgs
        user_orgs = ['']
        r = requests.get(
            controller_host + '/api/v2/users/' + str(user_id) + '/organizations?page=1&page_size=' + str(page_size),
            auth=(controller_user, controller_pass), verify=False)
        user_orgs_page1 = r.json()
        user_orgs_count = user_orgs_page1['count']
        user_orgs_pages_count = user_orgs_count // page_size + bool(user_orgs_count % page_size)

        if user_orgs_count > 0:
            print('+++ User ' + str(user_id) + ' belongs to ' + str(
                user_orgs_count) + ' Organization(s). Extracting it from ' + str(
                user_orgs_pages_count) + ' page(s).')
            for user_org_page_n in range(1, user_orgs_pages_count + 1):
                user_org_list_raw = requests.get(
                    controller_host + '/api/v2/users/' + str(user_id) + '/organizations?page=' + str(
                        user_org_page_n) + '&page_size=' + str(
                        page_size), auth=(controller_user, controller_pass), verify=False)
                user_org_list = user_org_list_raw.json()
                if user_org_list['results']:
                    for t in user_org_list['results']:
                        user_orgs.append(t['name'])

        # Removing empty first element
        if len(user_orgs) > 1 and user_orgs[0] == '':
            del user_orgs[0]

        result = str(
            user_id) + ';' + username + ';' + user_first_name + ';' + user_last_name + ';' + str(
            user_teams) + ';' + str(user_orgs) + ';' + user_ldap_dn + ';' + str(user_is_superuser)
        file.write(result + "\n")


def extract_inventories(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for inventory in page_n['results']:
        print("+ Extracting inventory " + str(inventory['id']) + ' details...')
        inventory_id = inventory['id']
        inventory_name = inventory['name']
        inventory_has_sources = inventory['has_inventory_sources']
        inventory_total_hosts = inventory['total_hosts']
        inventory_total_groups = inventory['total_groups']

        # Get kind
        if inventory['kind'] == 'smart':
            inventory_kind = 'Smart'
            inventory_host_filter = inventory['host_filter']
        else:
            inventory_kind = 'Normal'
            inventory_host_filter = 'Null'

        # Get Org
        if inventory['organization']:
            inventory_org = inventory['summary_fields']['organization']['name']
        else:
            inventory_org = 'Null'

        # Get Inventory Creator
        if 'created_by' in inventory['summary_fields']:
            if inventory['summary_fields']['created_by']['username']:
                inventory_creator = inventory['summary_fields']['created_by']['username']
            else:
                inventory_creator = 'Null'

        # Get last modified by
        if 'modified_by' in inventory['summary_fields']:
            if inventory['summary_fields']['modified_by']['username']:
                inventory_last_modified_by = inventory['summary_fields']['created_by']['username']
            else:
                inventory_last_modified_by = 'Null'


        inventory_sources_list = list()
        # Get inventory sources
        if inventory_has_sources:
            # Get sources count
            req = requests.get(
                controller_host + '/api/v2/' + resource + '/' + str(
                    inventory_id) + '/inventory_sources' + '?page=1&page_size=' + str(page_size),
                auth=(controller_user, controller_pass), verify=False)
            sources_page = req.json()
            source_count = sources_page['count']
            sources_pages_count = source_count // page_size + bool(source_count % page_size)

            if source_count > 0:
                print('++ Inventory ' + str(inventory_id) + ' has ' + str(source_count) + ' source(s) on ' + str(
                    sources_pages_count) + ' page(s) !')
                for source_page_n in range(1, sources_pages_count+1):
                    print('+++ Extracting sources page ' + str(source_page_n) + ' ...')
                    req = requests.get(
                        controller_host + '/api/v2/inventories/' + str(inventory_id) + '/inventory_sources' + '?page='+str(source_page_n)+'&page_size=' + str(page_size),
                        auth=(controller_user, controller_pass), verify=False)
                    sources_page = req.json()
                    for s in sources_page['results']:
                        inventory_source = {'source': s['name'], 'type': s['source']}
                        if s['summary_fields']['credentials']:
                            inventory_source['credential'] = list()
                            for cred in s['summary_fields']['credentials']:
                                inventory_source_credential_name = cred['name']
                                # inventory_source_credential_kind = cred['kind']
                                inventory_source['credential'].append(inventory_source_credential_name)
                                # inventory_source['credential'].append({inventory_source_credential_name, inventory_source_credential_kind})

                        if s['source_project']:
                            inventory_source['project_id'] = str(s['source_project'])

                        if s['summary_fields'].get('source_project') is not None :
                            inventory_source['project_name'] = s['summary_fields']['source_project']['name']

                        inventory_sources_list.append(inventory_source)

        result = str(inventory_id) + ';' + inventory_org + ';' + inventory_name + ';' + inventory_creator + ';' + inventory_last_modified_by + ';' + inventory_kind + ';' + str(
            inventory_total_hosts) + ';' + str(inventory_total_groups) + ';' + inventory_host_filter + ';' + str(
            inventory_has_sources) + ';' + str(inventory_sources_list)

        file.write(result + "\n")


def extract_roles(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for role in page_n['results']:

        if role['name'] == 'System Administrator' or role['name'] == 'System Auditor': #and not role['summary_fields']:
            role_id = role['id']
            role_name = role['name']
            resource_type = '*'
            resource_name = '*'
            role_teams_list_names = ['']
            print('+++ Extracting details of role ' + str(role_id))

            # Get System Administrator Or Auditor Role Users
            r = requests.get(
                 controller_host + '/api/v2/roles/' + str(role_id) + '/users?page=1&page_size=' + str(page_size),
                 auth=(controller_user, controller_pass), verify=False)
            admin_users_page1 = r.json()
            admin_users_count = admin_users_page1['count']
            admin_users_pages_count = admin_users_count // page_size + bool(admin_users_count % page_size)

            role_users_list_names = list()
            if admin_users_count > 0:
                print('++++ '+ role['name'] + ' role ' + str(role_id) + ' has ' + str(admin_users_count) + ' user(s) in ' + str(admin_users_pages_count) + ' page(s).')
                for user_n in range(1, admin_users_pages_count + 1):
                    role_users_list_raw = requests.get(
                        controller_host + '/api/v2/roles/' + str(role_id) + '/users?page=' + str(
                            user_n) + '&page_size=' + str(
                            page_size), auth=(controller_user, controller_pass), verify=False)
                    role_users_list = role_users_list_raw.json()
                    if role_users_list['results']:
                        for u in role_users_list['results']:
                            role_users_list_names.append(u['username'])

            if role_users_list_names:
                result = str(role_id) + ';' + resource_type + ';' + resource_name + ';' + role_name + ';' + str(
                    role_users_list_names) + ';' + str(role_teams_list_names)
                file.write(result + "\n")

        # Get Role target resource
        if role['summary_fields']:

            resource_name = role['summary_fields']['resource_name']
            resource_type = role['summary_fields']['resource_type_display_name']
            role_name = role['name']
            role_id = role['id']

            print('+++ Extracting details of role ' + str(role_id))
            # Get Role Users
            r = requests.get(
                controller_host + '/api/v2/roles/' + str(role_id) + '/users?page=1&page_size=' + str(page_size),
                auth=(controller_user, controller_pass), verify=False)
            user_page1 = r.json()
            user_count = user_page1['count']
            user_pages_count = user_count // page_size + bool(user_count % page_size)

            role_users_list_names = ['']
            if user_count > 0:
                print('++++ Role ' + str(role_id) + ' has ' + str(user_count) + ' user(s) in ' + str(
                    user_pages_count) + ' page(s).')
                for user_n in range(1, user_pages_count + 1):
                    role_users_list_raw = requests.get(
                        controller_host + '/api/v2/roles/' + str(role_id) + '/users?page=' + str(
                            user_n) + '&page_size=' + str(
                            page_size), auth=(controller_user, controller_pass), verify=False)
                    role_users_list = role_users_list_raw.json()
                    if role_users_list['results']:
                        for u in role_users_list['results']:
                            role_users_list_names.append(u['username'])

            # Removing empty first element
            if len(role_users_list_names) > 1 and role_users_list_names[0] == '':
                del role_users_list_names[0]

            # Get Role Teams

            r = requests.get(
                controller_host + '/api/v2/roles/' + str(role_id) + '/teams?page=1&page_size=' + str(page_size),
                auth=(controller_user, controller_pass), verify=False)
            teams_page1 = r.json()
            teams_count = teams_page1['count']
            teams_pages_count = teams_count // page_size + bool(teams_count % page_size)

            role_teams_list_names = ['']

            if teams_count > 0:
                print('++++ Role ' + str(role_id) + ' has ' + str(teams_count) + ' team(s) in ' + str(
                    teams_pages_count) + ' page(s).')
                for team_n in range(1, teams_pages_count + 1):
                    role_teams_list_raw = requests.get(
                        controller_host + '/api/v2/roles/' + str(role_id) + '/teams?page=' + str(
                            team_n) + '&page_size=' + str(
                            page_size), auth=(controller_user, controller_pass), verify=False)
                    role_teams_list = role_teams_list_raw.json()
                    if role_teams_list['results']:
                        role_teams_list_names = list()
                        for u in role_teams_list['results']:
                            role_teams_list_names.append(u['name'])

            # Removing empty first element
            # if len(role_teams_list_names) > 1 and role_teams_list_names[0] == '':
            #    del role_teams_list_names[0]

            # Keep result only if there is a user or a team attributed to the role
            if role_users_list_names != [''] or role_teams_list_names != ['']:
                result = str(role_id) + ';' + resource_type + ';' + resource_name + ';' + role_name + ';' + str(
                    role_users_list_names) + ';' + str(role_teams_list_names)
                file.write(result + "\n")



def extract_workflow_job_templates(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for wkfl in page_n['results']:
        # Get Hostname
        wkfl_id = wkfl['id']
        wkfl_name = wkfl['name']

        # Get Org
        if wkfl['organization']:
            wkfl_org = wkfl['organization']
        else:
            wkfl_org = 'Null'

        # Get Inventory
        if wkfl['inventory']:
            wkfl_inventory = wkfl['inventory']
        else:
            wkfl_inventory = 'Null'
        
        # Get limit
        if wkfl['limit']:
            wkfl_limit = wkfl['limit']
        else:
            wkfl_limit = 'Null'


        # Get wkfl Creator
        if wkfl['summary_fields']['created_by']['username']:
            wkfl_creator = wkfl['summary_fields']['created_by']['username']
        else:
            wkfl_creator = 'Null'

        # Get wkfl last modified by
        if wkfl['summary_fields']['modified_by']['username']:
            wkfl_last_modified_by = wkfl['summary_fields']['created_by']['username']
        else:
            wkfl_last_modified_by = 'Null'

        result = str(wkfl_id) + ';' + str(wkfl_org) + ';' + wkfl_name + ';' + str(wkfl_inventory) + ';' + wkfl_limit + ';' + wkfl_creator + ';' + wkfl_last_modified_by
        file.write(result + "\n")


def extract_job_templates(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()
    for jt in page_n['results']:
        # Get Hostname
        jt_id = jt['id']
        jt_name = jt['name']

        # Get Org
        if jt['organization']:
            jt_org = jt['summary_fields']['organization']['name']
        else:
            jt_org = 'Null'

        # Get Project
        if jt['project']:
            jt_project = jt['summary_fields']['project']['name']

        # Get Inventory
        if jt['inventory']:
            jt_inventory = jt['summary_fields']['inventory']['name']

        # Get Credentials
        jt_creds = list()
        if jt['summary_fields']['credentials']:
            for c in jt['summary_fields']['credentials']:
                jt_creds.append(c['name'])
        
        # Get limit
        if jt['limit']:
            jt_limit = jt['limit']
        else:
            jt_limit = 'Null'

        # Get JT Creator
        if jt['summary_fields']['created_by']['username']:
            jt_creator = jt['summary_fields']['created_by']['username']
        else:
            jt_creator = 'Null'

        # Get JT last modified by
        if jt['summary_fields']['modified_by']['username']:
            jt_last_modified_by = jt['summary_fields']['created_by']['username']
        else:
            jt_last_modified_by = 'Null'

        result = str(jt_id) + ';' + jt_org + ';' + jt_name + ';' + jt_project + ';' + str(jt_creds) + ';' + jt_inventory + ';' + jt_limit  + ';' + jt_creator + ';' + jt_last_modified_by
        file.write(result + "\n")


def extract_credentials(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for cred in page_n['results']:
        # Get Hostname
        cred_id = cred['id']
        cred_name = cred['name']

        # Get Org
        if cred['organization']:
            org = cred['summary_fields']['organization']['name']
        else:
            org = 'Null'

        # Get kind
        kind = cred['summary_fields']['credential_type']['name']

        # Get cred Created_by
        if 'created_by' in cred['summary_fields']:
            if cred['summary_fields']['created_by']['username']:
                cred_creator = cred['summary_fields']['created_by']['username']
            else:
                cred_creator = 'Null'

        # Get cred last modified by
        if 'modified_by' in cred['summary_fields']:
            if cred['summary_fields']['modified_by']['username']:
                cred_last_modified_by = cred['summary_fields']['created_by']['username']
            else:
                cred_last_modified_by = 'Null'

        # Getting access list to this cred
        # access_list_raw = requests.get(
        #     controller_host + '/api/v2/credentials/' + str(id) + '/access_list?page_size=200',
        #     auth=(controller_user, controller_pass), verify=False)
        # access_list = access_list_raw.json()

        result = str(cred_id) + ';' + org + ';' + cred_name + ';' + kind + ';' + cred_creator + ';' + cred_last_modified_by
        file.write(result + "\n")


def extract_projects(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for project in page_n['results']:
        # Get Hostname
        project_id = project['id']
        project_name = project['name']

        # Get Org
        if project['organization']:
            project_org = project['summary_fields']['organization']['name']
        else:
            project_org = 'Null'

        # Get Credentials
        if project['credential']:
            project_cred = project['summary_fields']['credential']['name']
        else:
            project_cred = 'Null'

        # Get Created_by
        if project['summary_fields']['created_by']['username']:
            project_creator = project['summary_fields']['created_by']['username']
        else:
            project_creator = 'Null'

        # Get last modified by
        if project['summary_fields']['modified_by']['username']:
            project_last_modified_by = project['summary_fields']['created_by']['username']
        else:
            project_last_modified_by = 'Null'

        result = str(project_id) + ';' + project_org + ';' + project_name + ';' + project_cred + ';' + project_creator + ';' + project_last_modified_by
        file.write(result + "\n")


def extract_host_metrics(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for host_metric in page_n['results']:
        # Get Hostname
        host_metric_id = host_metric['id']
        hostname = host_metric['hostname']
        automated_counter = host_metric['automated_counter']
        first_automation = host_metric['first_automation']
        last_automation = host_metric['last_automation']
        deleted_counter = host_metric['deleted_counter']
        deleted = host_metric['deleted']
        url = host_metric['url']

        # Get Credentials
        if host_metric['last_deleted']:
            last_deleted = host_metric['last_deleted']
        else:
            last_deleted = 'Null'

        # Get Created_by
        if host_metric['used_in_inventories']:
            used_in_inventories = host_metric['used_in_inventories']
        else:
            used_in_inventories = 'Null'

# 'host_metrics': 'host metric ID;hostname;automated_counter;deleted_counter;deleted;first_automation;last_automation;last_deleted;used_in_inventories;url'
        result = str(host_metric_id) + ';' + hostname + ';' + str(automated_counter) + ';' + str(deleted_counter) + ';' + str(deleted) + ';' + first_automation + ';' + last_automation + ';' + last_deleted + ';' + used_in_inventories + ';' + url
        file.write(result + "\n")


def extract_hosts(file, n):
    print("++ Page " + str(n) + ' / ' + str(pages_count) + '...')

    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()
    for host in page_n['results']:
        # Get Hostname
        host_id = host['id']
        hostname = host['name']
        org_id = str(host['summary_fields']['inventory']['organization_id'])
        vars = host['variables']

        # Get inventory of host
        inventory = host['summary_fields']['inventory']['name']

        # Get ansible_host varibale if it exist
        reg = r'ansible_host: (\S*)\b|\\\"ansible_host\\\": \\\"(.*?)\\\"'
        host_ansible_host_list = re.findall(reg, vars)
        if len(host_ansible_host_list) > 0:
            # Keep only non-empty tuples :
            host_ansible_host = [t for t in host_ansible_host_list[0] if t]
        else:
            host_ansible_host = ''

        # Get ansible_ssh_host variable if it exists
        reg = r'ansible_ssh_host: (\S*)\b|\\\"ansible_ssh_host\\\": \\\"(.*?)\\\"'
        host_ansible_ssh_host_list = re.findall(reg, vars)

        if len(host_ansible_ssh_host_list) > 0:
            # Keep only non-empty tuples :
            host_ansible_ssh_host_list = [t for t in host_ansible_ssh_host_list[0] if t]
        else:
            host_ansible_ssh_host = ''

        # Getting Org Name of inventory if "get_hosts_org_name" is set to True
        if get_hosts_org_name:
            org_raw = requests.get(controller_host + '/api/v2/organizations/' + org_id, auth=(controller_user, controller_pass), verify=False)
            org = org_raw.json()
            org = org['name']
        else:
            org = org_id

        result = str(host_id) + ';' + org + ';' + inventory + ';' + hostname + ';' + str(
            host_ansible_host) + ';' + str(host_ansible_ssh_host_list)
        file.write(result + "\n")

   
def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            if sock.connect_ex((host, port)) == 0:
                return True
            else:
                return False
        except:
            return False


def pre_flight_check():
    try: controller_fqdn
    except NameError:
        print('ERROR : Controller address or hostname or FQDN (controller_fqdn) is not defined ! Exiting.')
        exit(1)

    try: controller_user
    except NameError:
        print(f'ERROR : User (controller_user) is not defined ! Exiting.')
        exit(2)
    
    try: controller_pass
    except NameError:
        print(f'ERROR : Password (controller_pass) is not defined ! Exiting.')
        exit(3)

    try: controller_port
    except NameError:
        print(f'ERROR : Port (controller_port) is not defined ! Exiting.')
        exit(4)

    if not isinstance(controller_port, int):
        print(f"ERROR : Port (controller_port) should be an integer and not {type(page_size)} !")
        exit(5)

    try: page_size
    except NameError:
        print(f"ERROR : Page size (page_size) is not defined ! Please define it than rerun.")
        exit(6)

    if not isinstance(page_size, int):
        print(f"ERROR : Page size (page_size) should be an integer and not {type(page_size)} !")
        exit(7)

    if 0 > page_size or page_size > 200:
        print(f"ERROR : Page size (page_size) should be between 1 and 200 (and not {page_size}) !")
        exit(8)

    try: get_hosts_org_name
    except NameError:
        print(f"ERROR : get_hosts_org_name is not defined ! Please define it than rerun.")
        exit(9)


    if not isinstance(get_hosts_org_name, bool):
        print(f"ERROR : Page size (page_size) should be a boolean and not {type(get_hosts_org_name)} !")
        exit(10)

    if not resources_to_extract:
        print(f"ERROR : Resources to be extract (resources_to_extract) is not defined !")
        exit(11)

    if not isinstance(resources_to_extract, list):
        print(f"ERROR : Resources to be extract (resources_to_extract) should be a list and not {type(get_hosts_org_name)} !")
        exit(12)

    for res in resources_to_extract:
        if res not in all_possible_resources:
            print(f"ERROR : '{res}' is not a known resource. Should be one of : {all_possible_resources} !")
            exit(13)

    if not check_socket(controller_fqdn, controller_port):
        print(f'ERROR : Controller {controller_fqdn} unreachable on port {controller_port} ! Exiting.')
        exit(14)

    try:
        req1 = requests.get(f"https://{controller_fqdn}/api/v2/ping", verify=False)
        if req1.status_code > 299:
            print(f"ERROR : Controller API is not responding. Are you sure the controller address/FQDN is correct ?")
            exit(15)
    except:
        print(f"ERROR : Controller API is not responding. Are you sure the controller address/FQDN is correct ?")
        exit(16)

    req2 = requests.get(f"https://{controller_fqdn}/api/v2/me",auth=(controller_user, controller_pass), verify=False)
    if int(req2.status_code) > 299 :
        print(f"ERROR : User is not authorized. Please check the provided username and password !")
        exit(17)

    else:
        me = req2.json()
        if not me['results'][0]['is_superuser'] and not me['results'][0]['is_system_auditor']:
            print('')
            print('________________________________________________________________________________________________________________________________________________')
            print(f'!!    WARNING : The user "{controller_user}" is not system administrator or system auditor. The script will probably NOT extract everything    !!')
            print('________________________________________________________________________________________________________________________________________________')
            print('')

# Main
all_possible_resources = ['credentials', 'projects', 'hosts', 'job_templates', 'inventories', 'inventory_sources', 'users', 'teams',  'roles', 'workflow_job_templates', 'host_metrics']

pre_flight_check()

results_dir = 'results_' + controller_fqdn.replace(".", "_").lower()
controller_host = 'https://' + controller_fqdn + ':' + str(controller_port)

now = datetime.now()
print('')
print('########################################################################################')
print('###  STARTING EXTRACTION ')
print('###  Controller = "'+ str(controller_host)+'"')
print('###  Resource(s) to extract = '+str(resources_to_extract))
print('###  Date = ' + str(now))
print('########################################################################################')
print('')

# Create results directory if it does not exist
resultDirExist = os.path.exists(results_dir)
if not resultDirExist:
    os.makedirs(results_dir)

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(results_dir+"/extraction.log", "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        pass


sys.stdout = Logger()

headers = {
            'projects': 'Project ID;Organization;Project Name;Credential;Creator;Last Modified by',
            'hosts': 'Host ID;Organization;Inventory;Hostname;ansible_host;ansible_ssh_host',
            'credentials': 'Credential ID;Organization;Credential Name;Kind;Creator;Last Modified by',
            'job_templates': 'Job Template ID;Organization;Job Template Name;Project;Credentials;Inventory;limit;Creator;Last Modified by',
            'roles': 'Role ID;Object Type;Object Name;Role;Users;Teams',
            'inventories': 'Inventory ID;Organization;Inventory Name;Created By;Last Modified by;Inventory Kind;Total Hosts;Total Groups;Host Filter;Has Inventory Source;Inventory Sources Details',
            'users': 'User ID;Username;First Name;Last Name;Teams;Orgs;LDAP DN;Superuser',
            'teams': 'Team ID;Team Name;Organization;Users',
            'inventory_sources': 'Organization;Source Name;Source Type;Parent Inventory;Source Project;Source Credentials',
            'workflow_job_templates': 'Workflow ID;Organization;Workflow Name;Inventory;limit;Creator;Last Modified by',
            'host_metrics': 'host metric ID;hostname;automated_counter;deleted_counter;deleted;first_automation;last_automation;last_deleted;used_in_inventories;url'
        }

for resource in resources_to_extract:

    r = requests.get(controller_host + '/api/v2/' + resource + '?page=1&page_size=' + str(page_size),
                     auth=(controller_user, controller_pass), verify=False)
    page1 = r.json()
    count = page1['count']

    pages_count = count // page_size + bool(count % page_size)

    print('+ Extracting ' + resource + '....')
    print('+ There is a total of ' + str(count) + ' ' + resource + ' in ' + str(pages_count) + ' page(s) ! Extracting it all ...')

    f = open(results_dir + '/' + resource + '.csv', "w")
    f.write(headers[resource] + "\n")

    for x in range(1, (pages_count + 1)):
        getattr(sys.modules[__name__], "extract_%s" % resource)(f, x)

    print('+ ' + resource.upper() + " extraction complete. Results stored in : " + f.name)
    f.close()
    print('______________________________________________________________________________________________')


now = datetime.now()
print('')
print('########################################################################################')
print('###  EXTRACTION COMPLETE ')
print('###  Controller = "'+ str(controller_host)+'"')
print('###  Results directory = "' + results_dir + '"')
print('###  Extracted Resource(s) = '+str(resources_to_extract))
print('###  Date = ' + str(now))
print('########################################################################################')
print('')

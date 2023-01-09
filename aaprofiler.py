#!/usr/bin/python3

#############################################
#                                           #
#     Project : AAProfiler                  #
#     Author: Hamza Bouabdallah             #
#     Company: RedHat                       #
#     Version: 0.2                          #
#     LinkedIn: www.linkedin.com/in/w4hf    #
#     Github:  @w4hf                        #
#                                           #
#############################################

# This python Script scrape AWX or AAP Controller (Tower) API and Generate csv files Reports.
# The objects audited are :
# - credentials
# - projects
# - hosts
# - job_templates
# - roles
# - inventories
# Each object will have its own csv file generated under the 'results_dir'  (by default = 'results' )

import os
import math
import sys
import re
import requests

requests.packages.urllib3.disable_warnings()

# ------------------------ EDIT ONLY THIS BLOCK !!
controller_host = 'https://vip.aap'
controller_user = 'admin'
controller_pass = '**************'
page_size = 200
results_dir = "results"

# You can extract Everything :
resources_to_extract = ['credentials', 'projects', 'hosts', 'job_templates', 'roles', 'inventories', 'users', 'teams']

# OR You can pick and chose, for example to extract only hosts and projects :
# resources_to_extract = ['hosts', 'projects']

# -------------------------------------------- !! DO NOT EDIT ANYTHING BELOW THIS LINE !!

headers = {'projects': 'Project ID;Organization;Project Name;Credential',
           'hosts': 'Host ID;Organization;Inventory;Hostname;ansible_host;ansible_ssh_host',
           'credentials': 'Credential ID;Organization;Credential Name;Kind',
           'job_templates': 'Job Template ID;Organization;Job Template Name;Project;Credentials;Inventory',
           'roles': 'Role ID;Object Type;Object Name;Role;Users;Teams',
           'inventories': 'Inventory ID;Organization;Inventory Name;Total Hosts;Total Groups;Has Inventory Source',
           'users': 'User ID;Username;First Name;Last Name;Teams;Orgs;LDAP DN;Superuser',
           'teams': 'Team ID;Team Name;Organization;Users'
           }

# Create results directory if it does not exist
isExist = os.path.exists(results_dir)
if not isExist:
    os.makedirs(results_dir)


def extract_teams(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
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
        team_users_pages_count = math.ceil(team_users_count // page_size)
        if team_users_pages_count == 0:
            team_users_pages_count = 1

        if team_users_count > 0:
            print(' +++ Team ' + str(team_id) + ' has ' + str(
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
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
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
            user_is_superuser = 'Null'

        # Get user teams
        user_teams = ['']
        r = requests.get(
            controller_host + '/api/v2/users/' + str(user_id) + '/teams?page=1&page_size=' + str(page_size),
            auth=(controller_user, controller_pass), verify=False)
        user_teams_page1 = r.json()
        user_teams_count = user_teams_page1['count']
        user_teams_pages_count = math.ceil(user_teams_count // page_size)
        if user_teams_pages_count == 0:
            user_teams_pages_count = 1

        if user_teams_count > 0:
            print(' +++ User ' + str(user_id) + ' belongs to ' + str(
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
        user_orgs_pages_count = math.ceil(user_orgs_count // page_size)
        if user_orgs_pages_count == 0:
            user_orgs_pages_count = 1

        if user_orgs_count > 0:
            print(' +++ User ' + str(user_id) + ' belongs to ' + str(
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
            user_id) + ';' + username + ';' + user_first_name + ';' + user_last_name + ';' + str(user_teams) + ';' + str(user_orgs) + ';' + user_ldap_dn + ';' + str(user_is_superuser)
        file.write(result + "\n")


def extract_inventories(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for inventory in page_n['results']:

        inventory_id = inventory['id']
        inventory_name = inventory['name']
        inventory_has_source = inventory['has_inventory_sources']
        inventory_total_hosts = inventory['total_hosts']
        inventory_total_groups = inventory['total_groups']

        # Get Org
        if inventory['organization']:
            inventory_org = inventory['summary_fields']['organization']['name']
        else:
            inventory_org = 'Null'

        result = str(inventory_id) + ';' + inventory_org + ';' + inventory_name + ';' + str(
            inventory_total_hosts) + ';' + str(inventory_total_groups) + ';' + str(inventory_has_source)

        file.write(result + "\n")


def extract_roles(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()

    for role in page_n['results']:
        # Get Role target resource

        if role['summary_fields']:

            resource_name = role['summary_fields']['resource_name']
            resource_type = role['summary_fields']['resource_type_display_name']
            role_name = role['name']
            role_id = role['id']

            print(' + Extracting details of role ' + str(role_id))
            # Get Role Users
            r = requests.get(
                controller_host + '/api/v2/roles/' + str(role_id) + '/users?page=1&page_size=' + str(page_size),
                auth=(controller_user, controller_pass), verify=False)
            user_page1 = r.json()
            user_count = user_page1['count']
            user_pages_count = math.ceil(user_count // page_size)
            if user_pages_count == 0:
                user_pages_count = 1
            role_users_list_names = ['']
            if user_count > 0:
                print(' +++ Role ' + str(role_id) + ' has ' + str(user_count) + ' user(s) in ' + str(
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
            teams_pages_count = math.ceil(teams_count // page_size)
            if teams_pages_count == 0:
                teams_pages_count = 1
            role_teams_list_names = ['']

            if teams_count > 0:
                print(' +++ Role ' + str(role_id) + ' has ' + str(teams_count) + ' team(s) in ' + str(
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
            if len(role_teams_list_names) > 1 and role_teams_list_names[0] == '':
                del role_teams_list_names[0]

            # Keep result only if there is a user or a team attributed to the role
            if role_users_list_names != [''] or role_teams_list_names != ['']:
                result = str(role_id) + ';' + resource_type + ';' + resource_name + ';' + role_name + ';' + str(
                    role_users_list_names) + ';' + str(role_teams_list_names)
                file.write(result + "\n")


def extract_job_templates(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
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
        if jt['summary_fields']['credentials']:
            jt_creds = list()
            for c in jt['summary_fields']['credentials']:
                jt_creds.append(c['name'])

        result = str(jt_id) + ';' + jt_org + ';' + jt_name + ';' + jt_project + ';' + str(jt_creds) + ';' + jt_inventory
        file.write(result + "\n")


def extract_credentials(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
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

        # Getting access list to this cred
        access_list_raw = requests.get(
            controller_host + '/api/v2/credentials/' + str(id) + '/access_list?page_size=200',
            auth=(controller_user, controller_pass), verify=False)
        access_list = access_list_raw.json()

        result = str(cred_id) + ';' + org + ';' + cred_name + ';' + kind
        file.write(result + "\n")


def extract_projects(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')
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

        result = str(project_id) + ';' + project_org + ';' + project_name + ';' + project_cred
        file.write(result + "\n")


def extract_hosts(file, n):
    print("Page " + str(n) + ' / ' + str(pages_count) + '...')

    req = requests.get(controller_host + '/api/v2/' + resource + '?page=' + str(n) + '&page_size=' + str(page_size),
                       auth=(controller_user, controller_pass), verify=False)
    page_n = req.json()
    for host in page_n['results']:
        # Get Hostname
        host_id = host['id']
        hostname = host['name']
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

        # Get ansible_ssh_host variable if it exist
        reg = r'ansible_ssh_host: (\S*)\b|\\\"ansible_ssh_host\\\": \\\"(.*?)\\\"'
        host_ansible_ssh_host_list = re.findall(reg, vars)

        if len(host_ansible_ssh_host_list) > 0:
            # Keep only non-empty tuples :
            host_ansible_ssh_host_list = [t for t in host_ansible_ssh_host_list[0] if t]
        else:
            host_ansible_ssh_host = ''

        # Getting Org Name of inventory
        org_id = str(host['summary_fields']['inventory']['organization_id'])
        org_raw = requests.get(controller_host + '/api/v2/organizations/' + org_id,
                               auth=(controller_user, controller_pass), verify=False)
        org = org_raw.json()
        org_name = org['name']

        result = str(host_id) + ';' + org_name + ';' + inventory + ';' + hostname + ';' + str(
            host_ansible_host) + ';' + str(host_ansible_ssh_host_list)
        file.write(result + "\n")


for resource in resources_to_extract:

    r = requests.get(controller_host + '/api/v2/' + resource + '?page=1&page_size=' + str(page_size),
                     auth=(controller_user, controller_pass), verify=False)
    page1 = r.json()
    count = page1['count']

    pages_count = math.ceil(count // page_size)
    if pages_count == 0:
        pages_count = 1
    print('______________________________________________________________________________________________')
    print('Extracting ' + resource + '....')
    print('There is a total of ' + str(count) + ' ' + resource + ' in ' + str(
        pages_count) + ' pages ! Extracting it all ...')

    f = open(results_dir + '/' + resource + '.csv', "w")
    f.write(headers[resource] + "\n")

    for x in range(1, pages_count + 1):
        getattr(sys.modules[__name__], "extract_%s" % resource)(f, x)

    print(resource + " extraction complete. Results stored in : " + f.name)
    f.close()

print('______________________________________________________________________________________________')
print('')
print('###########################################################################')
print('###  Extraction complete results are under "' + results_dir + '" directory.')
print('###########################################################################')

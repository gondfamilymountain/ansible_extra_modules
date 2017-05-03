#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Stephen Fromm <sfromm@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: vmware_exsi
version_added: historical
short_description: Try to connect to exsi, get vms information.
description:
   - vmware module.
options:
    exsi:
        required: true
        description:
            - Ip of exsi.
    username:
        required: true
        aliases: [ "user" ]
        description:
            - User to connect to exsi.
    password:
        required: true
        description:
            - Password of user to connect to exsi.
author:
    - "Ansible Core Team"
'''

EXAMPLES = '''
 ansible all -m vmware_exsi -a "exsi=192.168.65.250 username=root password=password"
'''


import urllib2
import sys


def unrender_html(opener,url):
    urllib2.install_opener(opener)
    # All calls to urllib2.urlopen will now use our handler
    # Make sure not to include the protocol in with the URL, or
    # HTTPPasswordMgrWithDefaultRealm will be very confused.
    # You must (of course) use it when fetching the page though.
    
    pagehandle = urllib2.urlopen(url)
    # authentication is now handled automatically for 
    conent = pagehandle.read()
    return conent
 

# ===========================================


def main():
    module = AnsibleModule(
        argument_spec = dict(
            exsi=dict(required=True, type='str'),
            username=dict(required=True, type='str'),
            password=dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )
    exsi = module.params['exsi']
    username = module.params['username']
    password = module.params['password']
    srcurl = 'https://' + exsi
    theurl =  srcurl + '/folder'   
    
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    # this creates a password manager
    passman.add_password(None, theurl, username, password)
    # because we have put None at the start it will always
    # use this username/password combination for  urls
    # for which `theurl` is a super-url
    
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    # create the AuthHandler

    opener = urllib2.build_opener(authhandler)
    
    rootConent =  unrender_html(opener,theurl)
    
    final = {}
    final['virtual_machines']={}
    if 'href' in  rootConent:
         tmpurl1 =  rootConent.split('<a href="')[1].split('">')[0]
         tmpurl1 = srcurl + tmpurl1
         datastore_content = unrender_html(opener,tmpurl1)
         for data in  datastore_content.split('<a href="'):
            if 'dsName' in data:
                d_url = srcurl + data.split('">')[0].replace('amp;','')
                instance_content = unrender_html(opener,d_url)
                for i in instance_content.split('<a href="'):
                    if 'dsName' in i:
                        ins_url = srcurl + i.split('">')[0].replace('amp;','')
                        i_content = unrender_html(opener,ins_url)   
                        for k in i_content.split('<a href="'):
                            if 'dsName' in k:
                                k_url = srcurl + k.split('">')[0].replace('amp;','')    
                                render_kurl = k_url.replace('%2e','.')
                                if 'vmware.log' in render_kurl:
                                    r_content = unrender_html(opener,render_kurl)
                                    result = []
                                    for l in  r_content.split('\n'):
                                        if 'displayName' in l or 'allocationType' in l:
                                            result.append(l.rsplit('=',1)[1].strip())
                                    if result[1] == '0':
                                       final['virtual_machines'][result[0].strip('"')] = {'disk_type': 'thick'}
                                    elif result[1] == '1':
                                       final['virtual_machines'][result[0].strip('"')] = {'disk_type': 'flat'}
                                    elif result[1] == '2':
                                       final['virtual_machines'][result[0].strip('"')] = {'disk_type': 'thin'}
    module.exit_json(**final)
# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()



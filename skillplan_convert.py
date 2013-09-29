################################################################################################################################
#
#   skillplan_convert.py
#
#   Copyright (c) 2013; Mark Rogaski.
#
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions
#   are met:
#
#       * Redistributions of source code must retain the above copyright
#         notice, this list of conditions and the following disclaimer.
#
#       * Redistributions in binary form must reproduce the above
#         copyright notice, this list of conditions and the following
#         disclaimer in the documentation and/or other materials provided
#         with the distribution.
#
#       * Neither the name of the copyright holder nor the names of any
#         contributors may be used to endorse or promote products derived
#         from this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
###########################################################################################################

import argparse
import pprint
import xml.dom.minidom
from xml.dom.minidom import Node

def parse_tree(filename=None):
    tree = None
    
    if filename is not None:
        tree = { 'group': {}, 'skill': {} }
        doc = xml.dom.minidom.parse(filename)
        for group_set in doc.getElementsByTagName('rowset'):
            name = group_set.getAttribute('name')
            if name == 'skillGroups':
                for group_member in group_set.childNodes:
                    if group_member.nodeType == Node.ELEMENT_NODE:
                        # record group names
                        group_name = group_member.getAttribute('groupName')
                        group_id = group_member.getAttribute('groupID')
                        tree['group'][group_id] = { 'name': group_name }

                        # load skills
                        for skill_set in group_member.getElementsByTagName('rowset'):
                            name = skill_set.getAttribute('name')
                            if name == 'skills':
                                for skill_member in skill_set.childNodes:
                                    if skill_member.nodeType == Node.ELEMENT_NODE:
                                        skill_name = skill_member.getAttribute('typeName')  
                                        skill_id = skill_member.getAttribute('typeID')  
                                        skill_group = skill_member.getAttribute('groupID')
                                        tree['skill'][skill_id] = { 'name': skill_name, 'group': skill_group, 'desc': None, 'rank': None, 'attr': None, 'req': [], 'bonus': [] }
                                        for skill_elem in skill_member.childNodes:
                                            name = skill_elem.nodeName
                                            if name == 'description':
                                                tree['skill'][skill_id]['desc'] = skill_elem.firstChild.data
                                            elif name == 'rank':
                                                tree['skill'][skill_id]['rank'] = int(skill_elem.firstChild.data)
                                            elif name == 'requiredAttributes':
                                                pri_attr = skill_elem.getElementsByTagName('primaryAttribute').item(0)
                                                if pri_attr is not None:
                                                    pri_attr = pri_attr.firstChild.data
                                                sec_attr = skill_elem.getElementsByTagName('secondaryAttribute').item(0)
                                                if sec_attr is not None:
                                                    sec_attr = sec_attr.firstChild.data
                                                tree['skill'][skill_id]['attr'] = (pri_attr, sec_attr)
                                            elif name == 'rowset':
                                                name = skill_elem.getAttribute('name')
                                                if name == 'requiredSkills':
                                                    for req_elem in skill_elem.getElementsByTagName('row'):
                                                        req_id = req_elem.getAttribute('typeID')
                                                        req_level = int(req_elem.getAttribute('skillLevel'))
                                                        tree['skill'][skill_id]['req'].append((req_id, req_level))
                                                elif name == 'skillBonusCollection':
                                                    for bonus_elem in skill_elem.getElementsByTagName('row'):
                                                        bonus_type = bonus_elem.getAttribute('bonusType')
                                                        bonus_value = bonus_elem.getAttribute('bonusValue')
                                                        tree['skill'][skill_id]['bonus'].append((bonus_type, bonus_value))
                
    return tree


def main():
    parser = argparse.ArgumentParser(description='EVE Skillplan Converter')
    parser.add_argument('infiles', metavar='infile', nargs='+', help='input file')
    parser.add_argument('--tree', metavar='tree', nargs='?', help='CCP published skill tree')
    
    # Parse the command line
    args = parser.parse_args()
    
    # Build the skill tree data
    tree = parse_tree(args.tree)
    
    for file in args.infiles:
        doc = xml.dom.minidom.parse(file)
    
        for skill in doc.getElementsByTagName('skill'):
            name = skill.getAttribute('name')
            #pprint.pprint(name)
    


if __name__ == "__main__":
    main()
    


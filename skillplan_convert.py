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
from xml.etree.ElementTree import Element, SubElement, Comment, tostring


class SkillTree:
    """OO interface to the CCP skilltree."""
    skills = None
    groups = None
    
    def __init__(self, filename):
        if filename is not None:
            
            # Parse the XML
            doc = xml.dom.minidom.parse(filename)
            
            # Read group information at the top of the tree
            for group_set in doc.getElementsByTagName('rowset'):
                name = group_set.getAttribute('name')
                
                if name == 'skillGroups':
                
                    for group_member in group_set.childNodes:
                    
                        if group_member.nodeType == Node.ELEMENT_NODE:
                            # record group names
                            group_name = group_member.getAttribute('groupName')
                            group_id = group_member.getAttribute('groupID')
                            
                            if self.groups is None:
                                # Initialize the group data store.
                                self.groups = {}
                                
                            self.groups[group_id] = { 'name': group_name }

                            # Read skill data from deeper in the tree
                            for skill_set in group_member.getElementsByTagName('rowset'):
                                name = skill_set.getAttribute('name')
                                
                                if name == 'skills':
                                
                                    for skill_member in skill_set.childNodes:
                                    
                                        if skill_member.nodeType == Node.ELEMENT_NODE:
                                            skill_name = skill_member.getAttribute('typeName')  
                                            skill_id = skill_member.getAttribute('typeID')  
                                            skill_group = skill_member.getAttribute('groupID')
                                            
                                            if self.skills is None:
                                                # Initialize the skill data store.
                                                self.skills = {}
                                                
                                            self.skills[skill_id] = {'name': skill_name,
                                                                     'group': skill_group,
                                                                     'desc': None,
                                                                     'rank': None,
                                                                     'attr': None,
                                                                     'req': [],
                                                                     'bonus': [] }
                                        
                                            for skill_elem in skill_member.childNodes:
                                                name = skill_elem.nodeName
                                                
                                                if name == 'description':
                                                    self.skills[skill_id]['desc'] = skill_elem.firstChild.data
                                                
                                                elif name == 'rank':
                                                    self.skills[skill_id]['rank'] = int(skill_elem.firstChild.data)
                                                
                                                elif name == 'requiredAttributes':
                                                    pri_attr = skill_elem.getElementsByTagName('primaryAttribute').item(0)
                                                    if pri_attr is not None:
                                                        pri_attr = pri_attr.firstChild.data
                                                
                                                    sec_attr = skill_elem.getElementsByTagName('secondaryAttribute').item(0)
                                                    if sec_attr is not None:
                                                        sec_attr = sec_attr.firstChild.data
                                                    
                                                    self.skills[skill_id]['attr'] = (pri_attr, sec_attr)
                                                    
                                                elif name == 'rowset':
                                                    name = skill_elem.getAttribute('name')
                                                    
                                                    if name == 'requiredSkills':
                                                        for req_elem in skill_elem.getElementsByTagName('row'):
                                                            req_id = req_elem.getAttribute('typeID')
                                                            req_level = int(req_elem.getAttribute('skillLevel'))
                                                            
                                                            self.skills[skill_id]['req'].append((req_id, req_level))
                                                    
                                                    elif name == 'skillBonusCollection':
                                                        for bonus_elem in skill_elem.getElementsByTagName('row'):
                                                            bonus_type = bonus_elem.getAttribute('bonusType')
                                                            bonus_value = bonus_elem.getAttribute('bonusValue')
                                                            
                                                            self.skills[skill_id]['bonus'].append((bonus_type, bonus_value))

    def extend_plan(self, skills, id, level, compact=False):
        # Sanity checkind
        if skills is None:
            raise ValueError
    
        # Find prerequisites
        for req in self.skills[id]['req']:
            skills = self.extend_plan(skills, req[0], req[1], compact=compact)
    
        # Expand lower level versions of this skill, if necessary
        if level > 1 and not compact:
            skills = self.extend_plan(skills, id, level - 1, compact=compact)
    
        # Add this skill if it hasn't been added already
        if not [x for x in skills if id == x['id'] and level <= x['level']]:
            skills.append({'id': id, 'level': level})
        
        return skills

                    

def pformat(elem):
    ustr = tostring(elem, 'utf-8')
    dom = xml.dom.minidom.parseString(ustr)
    return dom.toprettyxml(indent='  ')


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


def extend_plan(skills, id, level, tree=None, noexpand=False):
    # Sanity checkind
    if skills is None or tree is None:
        raise ValueError
    
    # Find prerequisites
    for req in tree['skill'][id]['req']:
        skills = extend_plan(skills, req[0], req[1], tree=tree, noexpand=noexpand)
    
    # Expand lower level versions of this skill, if necessary
    if level > 1 and not noexpand:
        skills = extend_plan(skills, id, level - 1, tree=tree, noexpand=noexpand)
    
    # Add this skill if it hasn't been added already
    if not [x for x in skills if id == x['id'] and level <= x['level']]:
        skills.append({'id': id, 'level': level})
        
    return skills


def shopping_list(skills):
    s = set()
    for skill in skills:
        s.add(skill['id'])
    return list(s)


def main():

    # Parse the command line
    parser = argparse.ArgumentParser(description='EVE Skillplan Converter')
    parser.add_argument('infiles', metavar='infile', nargs='+', help='input file')
    parser.add_argument('--tree', metavar='tree', nargs='?', help='CCP published skill tree')
    parser.add_argument('--text', action='store_true', help='print text summary')
    parser.add_argument('--compact', action='store_true', help='do not expand skill levels')
    parser.add_argument('--name', metavar='name', nargs='?', help='skillplan name')
    parser.add_argument('--rev', nargs='?', default=0, help='skillplan revision')
    args = parser.parse_args()
    
    # Build the skill tree data
    tree = parse_tree(args.tree)

    # Top-level variables
    plan_name = args.name
    plan_revision = args.rev
    plan_skills = []
    plan_skills_seen = set()
    
    
    for infile in args.infiles:
        doc = xml.dom.minidom.parse(infile)
    
        root = doc.getElementsByTagName('SerializableCCPCharacter')
        if root:
            # After Plan Character
            for node in root.item(0).childNodes:
                if node.nodeName == 'name':
                    if plan_name is None:
                        plan_name = node.firstChild.data
                elif node.nodeName == 'skills':
                    for skill in node.getElementsByTagName('skill'):
                        name = skill.getAttribute('name')
                        id = skill.getAttribute('typeID')
                        level = int(skill.getAttribute('level'))
                        plan_skills = extend_plan(plan_skills, id, level, tree=tree, noexpand=args.compact)
                            
            break
        
        root = doc.getElementsByTagName('plan')
        if root:
            # Skill Plan
            break
    
    if args.text:
        # Build text
        print('Skill plan for %s\n' % plan_name)
        i = 1
        rom = [None, 'I', 'II', 'III', 'IV', 'V']
        
        for skill in plan_skills:
            print('%d. %s %s' % (i, tree['skill'][skill['id']]['name'], rom[skill['level']]))
            i = i + 1
        
        print('')
        print('%d unique skill(s), %d skill level(s)' % (len(shopping_list(plan_skills)), len(plan_skills)))   
        
    else:
        # Build XML
        plan = Element('plan')
        if plan_name is not None:
            plan.set('name', plan_name)
            if plan_revision is not None:
                plan.set('revision', '%d' % plan_revision)
        
        for skill in plan_skills:
            entry = SubElement(plan, 'entry')
            entry.set('skillID', skill['id'])
            entry.set('skill', tree['skill'][skill['id']]['name'])
            entry.set('level', '%d' % skill['level'])
            entry.set('priority', '3')
            entry.set('type', 'Planned')
            notes = SubElement(entry, 'notes')
            notes.text = plan_name

            print(pformat(plan))

if __name__ == "__main__":
    main()
    


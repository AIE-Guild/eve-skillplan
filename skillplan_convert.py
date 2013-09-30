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
__version__ = '0.1.0'
###########################################################################################################

import argparse
import xml.dom.minidom
import math
from xml.dom.minidom import Node
from xml.etree.ElementTree import Element, SubElement, tostring


class SkillTree:
    """OO interface to the CCP skilltree."""
    _baseline = {'all': [ ('3426', 3),
                          ('3413', 3),
                          ('3416', 2),
                          ('3300', 2),
                          ('3386', 2),
                          ('3392', 2),
                          ('3449', 3),
                          ('3402', 3),
                          ('3327', 3) ],
                 'amarr': [ ('3303', 3),
                            ('3331', 2) ],
                 'caldari': [ ('3301', 3),
                              ('3330', 2) ],
                 'gallente': [ ('3301', 3),
                               ('3328', 2) ],
                 'minmatar': [ ('3302', 3),
                               ('3329', 2) ]}
    skills = None
    groups = None
    attributes = {'intelligence': 20,
                  'perception': 20,
                  'charisma': 19,
                  'willpower': 20,
                  'memory': 20}

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

    def extend_plan(self, plan, skill, compact=False, race=None, baseline=True):
        
        def excluded(skill, punch_list):
            if [x for x in punch_list if skill[0] == x[0] and skill[1] <= x[1]]:
                return True
            else:
                return False
        
        # Sanity checking
        if plan is None:
            raise ValueError
    
        # Find prerequisites
        for req in self.skills[skill[0]]['req']:
            plan = self.extend_plan(plan, req, compact=compact, race=race, baseline=baseline)
    
        # Expand lower level versions of this skill, if necessary
        if skill[1] > 1 and not compact:
            plan = self.extend_plan(plan, (skill[0], skill[1] - 1), compact=compact, race=race, baseline=baseline)

        # Build the baseline
        if baseline:
            base = self._baseline['all']
            if race is not None:
                base = base + self._baseline[race]
        else:
            base = []
    
        # Add this skill if it hasn't been added already
        if not excluded(skill, plan):
            if not excluded(skill, base):
                plan.append(skill)
        
        return plan

    def training_time(self, sid, level):
        rank = self.skills[sid]['rank']
        base = 250 * rank * math.sqrt(32) ** (level - 1)
        if level > 1:
            base = base - (250 * rank * math.sqrt(32) ** (level - 2))
            
        (primary, secondary) = self.skills[sid]['attr']
        t = int((base / (self.attributes[primary] + (self.attributes[secondary] / 2))) * 60)
        return t
    
    def skill_name(self, sid):
        return self.skills[sid]['name']

    def group_name(self, sid):
        return self.groups[sid]['name']


def pformat(elem):
    ustr = tostring(elem, 'utf-8')
    dom = xml.dom.minidom.parseString(ustr)
    return dom.toprettyxml(indent='  ')

def format_time(s):
    m = s / 60
    s = s % 60
    h = m / 60
    m = m % 60
    d = h / 24
    h = h % 24
    
    elem = []
    
    if d == 1:
        elem.append('1 day')
    elif d > 1:
        elem.append('%s days' % d)
    
    if h == 1:
        elem.append('1 hour')
    elif h > 1:
        elem.append('%d hours' % h)
    
    if m == 1:
        elem.append('1 minute')
    elif m > 1: 
        elem.append('%d minutes' % m)
    
    if s == 1:
        elem.append('1 second')
    elif s > 1:
        elem.append('%d seconds' % s)
    
    return ', '.join(elem)
        
def shopping_list(skills):
    s = set()
    for skill in skills:
        s.add(skill[0])
    return list(s)

def main():

    # Parse the command line
    parser = argparse.ArgumentParser(description='EVE Skillplan Converter')
    parser.add_argument('infiles', type=file, metavar='INFILE', nargs='+', action='store', help='input file')
    parser.add_argument('--tree', type=file, nargs=1, action='store', help='CCP published skill tree')
    parser.add_argument('--text', action='store_true', help='print text summary')
    parser.add_argument('--compact', action='store_true', help='do not expand skill levels')
    parser.add_argument('--name', nargs=1, action='store', help='skillplan name')
    parser.add_argument('--rev', type=int, nargs=1, action='store', default=0, help='skillplan revision')
    parser.add_argument('--race', nargs=1, action='store', help='character race', choices=['amarr', 'caldari', 'gallente', 'minmatar'])
    parser.add_argument('--baseline', action='store_true', help='do not include starting skills')
    parser.add_argument('--priority', type=int, nargs=1, action='store', default=3, help='default priority', choices=[1, 2, 3, 4, 5])
    args = parser.parse_args()
    
    # Build the skill tree data
    skill_tree = SkillTree(args.tree[0])


    
    # Top-level variables
    plan_name = args.name
    plan_revision = args.rev
    plan_skills = []
    plan_priority = {}
    
    
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
                        sid = skill.getAttribute('typeID')
                        level = int(skill.getAttribute('level'))
                        plan_skills = skill_tree.extend_plan(plan_skills, (sid, level), compact=args.compact, race=args.race, baseline=args.baseline)
                            
            break
        
        root = doc.getElementsByTagName('plan').item(0)
        if root:
            # Skill Plan
            if plan_name is None:
                plan_name = root.getAttribute('name')
            if plan_revision is None:
                plan_revision = root.getAttribute('revision')
                
            for node in root.childNodes:
                if node.nodeName == 'entry':
                    sid = node.getAttribute('skillID')
                    level = int(node.getAttribute('level'))
                    skill = (sid, level)
                    
                    # Record the lowest priority value
                    priority = int(node.getAttribute('priority'))
                    try:
                        if plan_priority[skill] > priority:
                            plan_priority[skill] = priority
                    except:
                        plan_priority[skill] = priority
                        
                    plan_skills = skill_tree.extend_plan(plan_skills, skill, compact=args.compact, race=args.race, baseline=args.baseline)
                
            break
    
    if args.text:
        # Build text
        print('Skill plan for %s\n' % plan_name)
        i = 1
        rom = [None, 'I', 'II', 'III', 'IV', 'V']
        
        plan_time = 0
        for skill in plan_skills:
            skill_time = skill_tree.training_time(skill[0], skill[1])
            plan_time = plan_time + skill_time
            print('%d. %s %s (%s)' % (i, skill_tree.skill_name(skill[0]), rom[skill[1]], format_time(skill_time)))
            i = i + 1
        
        skill_list = shopping_list(plan_skills)
        if len(skill_list) == 1:
            unique_str = '1 unique skill'
        else:
            unique_str = '%d unique skills' % len(skill_list)
            
        if len(plan_skills) == 1:
            level_str = '1 skill level'
        else:
            level_str = '%d skill levels' % len(plan_skills)
            
        print('')
        print('%s, %s; Total time: %s' % (unique_str, level_str, format_time(plan_time)))   
        
    else:
        # Build XML
        plan = Element('plan')
        if plan_name is not None:
            plan.set('name', plan_name)
            if plan_revision is not None:
                plan.set('revision', '%d' % plan_revision)
        
        for skill in plan_skills:
            entry = SubElement(plan, 'entry')
            entry.set('skillID', skill[0])
            entry.set('skill', skill_tree.skill_name(skill[0]))
            entry.set('level', '%d' % skill[1])
            entry.set('type', 'Planned')

            try:
                priority = plan_priority[skill]
            except:
                priority = args.priority
            entry.set('priority', '%d' % priority)

            notes = SubElement(entry, 'notes')
            notes.text = plan_name

        print(pformat(plan))

if __name__ == "__main__":
    main()
    


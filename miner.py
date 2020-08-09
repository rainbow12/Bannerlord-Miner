import xmlschema
from pprint import pprint

mb_folder = 'C:\Program Files (x86)\Steam\steamapps\common\Mount & Blade II Bannerlord'

xs_item_modifiers = xmlschema.XMLSchema(mb_folder + '\XmlSchemas\ItemModifiers.xsd')
modifiers = xs_item_modifiers.to_dict(mb_folder + r'\Modules\Native\ModuleData\item_modifiers.xml')
xs_modifier_groups = xmlschema.XMLSchema(mb_folder + '\XmlSchemas\ItemModifierGroups.xsd')
modifier_groups = xs_modifier_groups.to_dict(mb_folder + r'\Modules\Native\ModuleData\item_modifiers_groups.xml')
xs_items = xmlschema.XMLSchema(mb_folder + '\XmlSchemas\Items.xsd')
items = xs_items.to_dict(mb_folder + '\Modules\SandBoxCore\ModuleData\spitems.xml')

types = set()
for item in items['Item']:
    types.add(item['@Type'])


def normalize_name(s):
    pieces = s.split('_')
    pieces[0] = pieces[0].replace('@', '')  # remove @
    pieces = map(lambda a: "".join(c.upper() if i == 0 else c for i, c in enumerate(a)),
                 pieces)  # capitalize first letters
    return " ".join(pieces)


def remove_hash(s):
    i = s.find('}')
    return s[i + 1:len(s)]


def get_modifier_name(s):
    i = s.find('}')
    s = s[i + 1: len(s)]
    i = s.find(' ')
    s = s[0:i]
    return s


def get_culture(s):
    if len(s) > 0:
        i = s.find('.')
        s = s[i + 1: len(s)]
        return "".join(c.upper() if i == 0 else c for i, c in enumerate(s))
    else:
        return ""


def find_modifier(mod_id, modifiers):
    for modifier in modifiers['ItemModifier']:
        if modifier['@id'] == mod_id:
            return modifier


def get_modifier(pgroup, modifier_groups, modifiers):
    s = ''
    for group in modifier_groups['ItemModifierGroups']:
        if group['@id'] == pgroup:
            for modifier in group['ItemModifier']:
                mod = find_modifier(modifier, modifiers)
                s += '{} '.format(get_modifier_name(mod['@name']))


def convert_modifier_hell(modifiers, modifier_groups):
    good_mods_groups = {}
    for group in modifier_groups['ItemModifierGroup']:
        group_dict = {}
        for mod_id in group['ItemModifier']:
            mod = {}
            mod['Probabilty'] = mod_id['@probability']
            for moddd in modifiers['ItemModifier']:
                if moddd['@id'] == mod_id['@id']:
                    for attribute in moddd:
                        if attribute == '@name':
                            mod[normalize_name(attribute)] = get_modifier_name(moddd[attribute])
                        elif attribute != '@id':
                            mod[normalize_name(attribute)] = moddd[attribute]

            group_dict[mod_id['@id']] = mod
        good_mods_groups[group['@id']] = group_dict

    return good_mods_groups


class Miner:
    def __init__(self, items, modifiers, getters, item_type):
        self.items = items
        self.modifiers = modifiers
        self.getters = getters
        self.item_type = item_type
        self.s = ''

    def get_result(self):
        return self.s

    def make_subdivided_row(self, item):
        s = ''
        max_subrow = 1
        for header, sub_getters in self.getters:
            max_subrow = max(len(sub_getters), max_subrow)

        rowspan_string = ""
        if max_subrow > 1:
            rowspan_string = 'rowspan="{}"|'.format(max_subrow)

        # do first row it has all the multi row entries
        s += '|-\n'
        s += '|{}{}\n'.format(rowspan_string, self.getters[0][1][0](item))
        for header, sub_getters in self.getters[1:]:
            if len(sub_getters) > 1:
                s += '|{}\n'.format(sub_getters[0][1])
                s += '|{}\n'.format(sub_getters[0][0](item))
            else:
                s += '|{}{}\n'.format(rowspan_string, sub_getters[0](item))

        # these only fill the "gaps"
        for i in range(1, max_subrow):
            s += '|-\n'
            for header, sub_getters in self.getters:
                if i < len(sub_getters):
                    s += '|{}\n'.format(sub_getters[i][1])
                    s += '|{}\n'.format(sub_getters[i][0](item))
        return s

    def make_table(self):
        # self.s = '<onlyinclude><div class="mw-customtoggle-helmets wikia-menu-button">Show/Hide {}</div>\n'.format(self.item_type)

        self.s += '<!-- Github link for the python script: https://github.com/rainbow12/Bannerlord-Miner -->\n'
        self.s += 'These tables are generated from game data. Do not edit this page. the Temp:* pages are intended' \
                 ' as temporary resource that are continually updated. Once the game is finalized, these can be deleted ' \
                 'and replaced with non-ugly ones :P (Game Version: e1.4.3)\n'
        #self.s += '<div class="mw-collapsible mw-collapsed">\n'
        self.s += '<div class="mw-collapsible">\n'
        self.s += '=={}==\n'.format(normalize_name(self.item_type))
        self.s += '<div class="mw-collapsible-content">\n'
        self.s += '{| class="sortable collapsible wikitable" style="text-align:center;"\n'
        for i, (header, sub_getters) in enumerate(self.getters):
            if len(self.getters[i][1]) > 1:
                self.s += '!colspan="2"|{}\n'.format(header)
            else:
                self.s += '!{}\n'.format(header)

        for item in self.items['Item']:
            if item['@Type'] == self.item_type:
                self.s += self.make_subdivided_row(item)

        self.s += '|}\n'
        self.s += '</div></div>\n\n'

        return self.s

    def make_modifier_tables(self):

        self.s += "=Modifiers=\n"

        groups = set()
        for item in self.items['Item']:
            if item['@Type'] == self.item_type:
                groups.add(item['ItemComponent'][0]['Armor'][0]['@modifier_group'])

        # headers
        groups = list(groups)

        for group_id in groups:
            self.s += '<div class="mw-collapsible">\n'
            self.s += '==={}===\n'.format(group_id)
            self.s += '<div class="mw-collapsible-content">\n'
            self.s += '{| class="sortable collapsible wikitable" style="text-align:center;"\n'
            self.s += '|+{}\n'.format(normalize_name(group_id))

            atts = []
            for mod_id in self.modifiers[group_id]:
                for attribute in self.modifiers[group_id][mod_id]:
                    atts += [attribute]
                    self.s += '! {}\n'.format(attribute)
                break

            for mod_id in self.modifiers[group_id]:
                self.s += '|-\n'
                for attribute in atts:
                    if attribute not in self.modifiers[group_id][mod_id]:
                        self.s += '|\n'
                    else:
                        self.s += '| {}\n'.format(self.modifiers[group_id][mod_id][attribute])

            self.s += '|}\n'
            self.s += '</div></div>\n\n'


good_mod_groups = convert_modifier_hell(modifiers, modifier_groups)

attribute_getters_head = [
    ('Item', [lambda item: remove_hash(item['@name'])]),
    ('Armor', [lambda item: item['ItemComponent'][0]['Armor'][0]['@head_armor']]),
    ('Material', [lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
    ('Weight', [lambda item: str(item['@weight'])]),
    ('Modifiers', [lambda item: '[[#'+item['ItemComponent'][0]['Armor'][0]['@modifier_group']+']]']),
    ('Culture', [lambda item: get_culture(item['@culture'])]),
]

# attribute_getters_body = [
#     ('Item',[lambda item: remove_hash(item['@name'])]),
#     ('Armor',[(lambda item: item['ItemComponent'][0]['Armor'][0].get('@arm_armor', ""), "Arm"),
#    (lambda item: item['ItemComponent'][0]['Armor'][0]['@body_armor'], "Body"),
#     (lambda item: item['ItemComponent'][0]['Armor'][0]['@leg_armor'], "Leg")
#     ]),
#     ("Material",[lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
#    ('Weight',[lambda item: str(item['@weight'])]),
# ]

attribute_getters_body = [
    ('Item', [lambda item: remove_hash(item['@name'])]),
    ('Armor Arm', [lambda item: item['ItemComponent'][0]['Armor'][0].get('@arm_armor', "")]),
    ('Armor Body', [lambda item: item['ItemComponent'][0]['Armor'][0]['@body_armor']]),
    ('Armor Leg', [lambda item: item['ItemComponent'][0]['Armor'][0]['@leg_armor']]),
    ('Material', [lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
    ('Weight', [lambda item: str(item['@weight'])]),
    ('Modifiers', [lambda item: '[[#'+item['ItemComponent'][0]['Armor'][0]['@modifier_group']+']]']),
    ('Culture', [lambda item: get_culture(item['@culture'])]),
]

attribute_getters_cape = [
    ('Item', [lambda item: remove_hash(item['@name'])]),
    ('Armor Arm', [lambda item: item['ItemComponent'][0]['Armor'][0].get('@arm_armor', "")]),
    ('Armor Body', [lambda item: item['ItemComponent'][0]['Armor'][0].get('@body_armor', "")]),
    ('Material', [lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
    ('Weight', [lambda item: str(item['@weight'])]),
    ('Modifiers', [lambda item: '[[#'+item['ItemComponent'][0]['Armor'][0]['@modifier_group']+']]']),
    ('Culture', [lambda item: get_culture(item['@culture'])]),
]

attribute_getters_leg = [
    ('Item', [lambda item: remove_hash(item['@name'])]),
    ('Armor Leg', [lambda item: item['ItemComponent'][0]['Armor'][0].get('@leg_armor', "")]),
    ('Material', [lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
    ('Weight', [lambda item: str(item['@weight'])]),
    ('Modifiers', [lambda item: '[[#'+item['ItemComponent'][0]['Armor'][0]['@modifier_group']+']]']),
    ('Culture', [lambda item: get_culture(item['@culture'])]),
]

attribute_getters_arm = [
    ('Item', [lambda item: remove_hash(item['@name'])]),
    ('Armor Hand', [lambda item: item['ItemComponent'][0]['Armor'][0].get('@arm_armor', "")]),
    ('Material', [lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
    ('Weight', [lambda item: str(item['@weight'])]),
    ('Modifiers', [lambda item: '[[#'+item['ItemComponent'][0]['Armor'][0]['@modifier_group']+']]']),
    ('Culture', [lambda item: get_culture(item['@culture'])]),
]

attribute_getters_harness = [
    ('Item', [lambda item: remove_hash(item['@name'])]),
    ('Armor Body', [lambda item: item['ItemComponent'][0]['Armor'][0].get('@body_armor', "")]),
    ('Material', [lambda item: item['ItemComponent'][0]['Armor'][0]['@material_type']]),
    ('Weight', [lambda item: str(item['@weight'])]),
    ('Modifiers', [lambda item: '[[#'+item['ItemComponent'][0]['Armor'][0]['@modifier_group']+']]']),
]

miners = [Miner(items, good_mod_groups, attribute_getters_head, 'HeadArmor'),
          Miner(items, good_mod_groups, attribute_getters_body, 'BodyArmor'),
          Miner(items, good_mod_groups, attribute_getters_cape, 'Cape'),
          Miner(items, good_mod_groups, attribute_getters_leg, 'LegArmor'),
          Miner(items, good_mod_groups, attribute_getters_arm, 'HandArmor'),
          Miner(items, good_mod_groups, attribute_getters_harness, 'HorseHarness')
          ]

for miner in miners:
    with open('{}.txt'.format(miner.item_type), "w") as f:
        miner.make_table()
        miner.make_modifier_tables()
        f.write(miner.get_result())

# pprint(modifiers)
# pprint(modifier_groups)
# print(types)
# print(s_body)

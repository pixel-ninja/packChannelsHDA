import os
import re

import hou

_NAMESPACE = 'PixelNinja'
_NAME = 'packChannels'
_LABEL = 'Pack Channels'
_VERSION = "0.0.1"

_ROOT_PATH = os.path.dirname(__file__)

_INPUT_LABEL_EXPR = re.compile(r"^label(\d+)$")


# Helpers
def _read_file(file_name: str) -> str:
	'''Return contents of a file relative to this script as a string.'''
	with open(os.path.join(file_name), 'r') as file:
		return file.read()


def _create_hda(parent: hou.Node) -> hou.Node:
	'''Create an hda from a subnet.'''
	subnet = parent.createNode('subnet', _NAME)

	type_name = hou.hda.fullNodeTypeNameFromComponents(
		scope_node_type= '',
		name_space= _NAMESPACE,
		name= _NAME,
		version= _VERSION
	)
	
	hda_path = os.path.join(_ROOT_PATH, 'build', f'{type_name.replace("::", ".")}.hda')

	# Rename input labels
	for parm in subnet.parms():
		match = _INPUT_LABEL_EXPR.match(parm.name())
		if match is None:
			continue

		digit = match.group(1)
		parm.set(f'Input {digit}')

	return subnet.createDigitalAsset(
		name= type_name,
		hda_file_name= hda_path,
		description= _LABEL,
		min_num_inputs= 1,
		max_num_inputs= 1,
		compress_contents= True,
		change_node_type= True,
		create_backup= False,
	)

def _attrParmTemplate(name: str, size: int, suffix: str = '') -> hou.FolderParmTemplate:
	return hou.FolderParmTemplate(
		f'{name}{suffix}',
		f'{name}{suffix}',
		folder_type= hou.folderType.Simple,
		tags= {"group_type": "simple", "sidefx::look": "blank"},
		parm_templates= [
			hou.MenuParmTemplate(
				f'{name}_{x}{suffix}',
				f'{name}{suffix}',
				[],
				is_label_hidden= x > 0,
				join_with_next= True,
				item_generator_script= 'hou.pwd().hm().component_menu_list(kwargs)',
				item_generator_script_language=hou.scriptLanguage.Python,
			) for x in range(size)
		]
	)


def _build_parms() -> tuple[hou.ParmTemplate, ...]:
	'''Returns list of parameters for hda UI.'''

	buttons = (
		('P', 3),
		('N', 3),
		('Cd', 4),
		('uv', 2),
		('uv1', 2),
		('uv2', 2),
		('uv3', 2),
		('uv4', 2),
		('uv5', 2),
		('uv6', 2),
		('uv7', 2),
	)

	button_labels = [x[0] for x in buttons]

	return (
		# Global Parameters
		hou.FolderParmTemplate(
			'options',
			'Attributes',
			folder_type= hou.folderType.Simple,
			parm_templates= (
				hou.MenuParmTemplate(
					'class',
					'Class',
					['points', 'vertices'],
				),
				hou.StringParmTemplate(
					'attributes',
					'Attributes',
					1,
					menu_type= hou.menuType.StringToggle,
					item_generator_script= 'hou.pwd().hm().attribute_menu_list(kwargs)',
					item_generator_script_language= hou.scriptLanguage.Python,
					script_callback= 'hou.pwd().hm().validSelectedAttributes(kwargs["node"])',
					script_callback_language= hou.scriptLanguage.Python,
				),
			),
		),
		# Geometry Attribute Parameters
		hou.FolderParmTemplate(
			'packing_geometry',
			'Geometry',
			folder_type= hou.folderType.Simple,
			parm_templates= (
				hou.ToggleParmTemplate(
					'enable_geometry',
					'Enable',
					default_value= True
				),
				hou.FolderParmTemplate(
					'packing_attributes_parms',
					'',
					folder_type= hou.folderType.Simple,
					tags= {"group_type": "simple", "sidefx::look": "blank"},
					conditionals= { hou.parmCondType.HideWhen: '{ enable_geometry == 0 }' },
					parm_templates= (
						hou.MenuParmTemplate(
							'channels',
							'Channels',
							[],
							is_button_strip= True,
							menu_type=hou.menuType.StringToggle,
							item_generator_script= str(sum(zip(button_labels, button_labels), ())),
							item_generator_script_language=hou.scriptLanguage.Python,
							default_value= int('001'[::-1], 2),
							script_callback= 'hou.pwd().hm().toggle_attributes(kwargs)',
							script_callback_language= hou.scriptLanguage.Python,
						),
						hou.SeparatorParmTemplate('channel_separator'),
						*(_attrParmTemplate(x[0], x[1]) for x in buttons),
					),
				),
			),
		),
		# Texture Attribute Parameters
		hou.FolderParmTemplate(
			'packing_texture',
			'Texture',
			folder_type= hou.folderType.Simple,
			parm_templates= (
				hou.ToggleParmTemplate('enable_texture',
					'Enable',
					default_value= False
				),
				hou.FolderParmTemplate(
					'packing_texture_parms',
					'',
					folder_type= hou.folderType.Simple,
					tags= {"group_type": "simple", "sidefx::look": "blank"},
					conditionals= { hou.parmCondType.HideWhen: '{ enable_texture == 0 }' },
					parm_templates= (
						hou.ButtonParmTemplate(
							'save_texture',
							'Save to Disk',
							script_callback= 'hou.pwd().hm().saveTexture()',
							script_callback_language= hou.scriptLanguage.Python,
						),
						hou.MenuParmTemplate(
							'height',
							'Size',
							menu_items= ('smallest', 'square'),
							script_callback= 'hou.pwd().hm().calculateOutputSize(kwargs["node"])',
							script_callback_language= hou.scriptLanguage.Python,
							join_with_next= True,
						),
						hou.LabelParmTemplate(
							'output_size_label',
							'Output Size',
							is_label_hidden= True,
							column_labels= (['`chs("output_sizex")` x `chs("output_sizey")` pixels']),
						),
						hou.StringParmTemplate(
							'output',
							'Output File',
							1,
							default_value= (['$HIP/tex/${OS}_{attrs}.exr']),
							string_type=hou.stringParmType.FileReference,
							file_type=hou.fileType.Image,
							tags= {"filechooser_mode": "write"},
						),
						hou.IntParmTemplate(
							'output_size',
							'Output Size',
							3,
							is_hidden= True,
						),
						hou.StringParmTemplate(
							'uvattrib',
							'UV Attribute',
							1,
							default_value= (['uv1']),
						),
						hou.FolderParmTemplate(
							'texture_multiparm',
							'Pixel Rows/Values',
							folder_type= hou.folderType.MultiparmBlock,
							script_callback= 'hou.pwd().hm().calculateOutputSize(kwargs["node"])',
							script_callback_language= hou.scriptLanguage.Python,
							parm_templates= [_attrParmTemplate('Row', 4, suffix='_#')],
						),
					),
				),
			),
		),
	)


def _build_hda_network(parent: hou.Node) -> None:
	'''Builds network inside of hda for assigning attribute values.'''

	# TEXTURE BRANCH
	# Python sop for updating texture size
	python_calculate_output = parent.createNode('python', 'calculate_texture_size')
	python_calculate_output.parm('python').set("node = hou.parent()\nnode.hm().calculateOutputSize(node)")
	python_calculate_output.setInput(0, parent.indirectInputs()[0])

	# Wrangle for creating data uvs
	wrangle_uv_node = parent.createNode("attribwrangle", "data_uv_coordinates")
	wrangle_uv_node.parm('class').setExpression('ch("../class")+2')
	wrangle_uv_node.parm('snippet').set(_read_file('dataUVCoordinates.vfl'))
	wrangle_uv_node.setInput(0, python_calculate_output)

	# Switch for enabling writing attributes to texture
	switch_texture_node = parent.createNode('switch', 'switch_texture')
	switch_texture_node.setInput(0, parent.indirectInputs()[0])
	switch_texture_node.setInput(1, wrangle_uv_node)
	switch_texture_node.parm('input').setExpression('ch("../enable_texture")')

	# GEO BRANCH
	# Wrangle for assigning components to point/vector attributes
	wrangle_assign_components_node = parent.createNode("attribwrangle", "assign_components")
	wrangle_assign_components_node.parm('snippet').set(_read_file('assignComponents.vfl'))
	wrangle_assign_components_node.parm('class').setExpression('ch("../class")+2')
	wrangle_assign_components_node.setInput(0, switch_texture_node)

	# Switch for enabling writing attributes to geometry
	switch_geometry_node = parent.createNode('switch', 'switch_geometry')
	switch_geometry_node.setInput(0, switch_texture_node)
	switch_geometry_node.setInput(1, wrangle_assign_components_node)
	switch_geometry_node.parm('input').setExpression('ch("../enable_geometry")')

	
	output_node = parent.createNode('output')
	output_node.setInput(0, switch_geometry_node)
	
	parent.layoutChildren()


def build() -> hou.Node:
	# Create sop container to house sop hda
	root = hou.node('/obj')
	parent = root.createNode('geo')

	hda_node = _create_hda(parent)
	definition = hda_node.type().definition()
	definition.setVersion(_VERSION)
	
	definition.addSection(
		'PythonModule',
		_read_file('PythonModule.py')
		)
	definition.setExtraFileOption('PythonModule/IsPython', True)
	
	definition.addSection(
		'OnCreated',
		'kwargs["node"].hm().toggle_attributes(kwargs)'
		)
	definition.setExtraFileOption('OnCreated/IsPython', True)

	parms = _build_parms()
	parm_template_group = hou.ParmTemplateGroup(parms)

	definition.setParmTemplateGroup(parm_template_group)
	hda_node.parm('channels').set(15)

	_build_hda_network(hda_node)
	definition.updateFromNode(hda_node)


if __name__ == '__main__':
	build()
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


def _build_parms() -> tuple[hou.ParmTemplate, ...]:
	'''Returns list of parameters for hda UI.'''

	button_labels = ['P', 'N', 'Cd']
	button_labels.extend([f'uv{x if x > 1 else ""}' for x in range(1, 9)])
	button_items = [str(x) for x in range(len(button_labels))]

	return (
		hou.MenuParmTemplate(
		'channels',
		'Channels',
		[],
		is_button_strip= True,
		menu_type=hou.menuType.StringToggle,
		item_generator_script= str(sum(zip(button_items, button_labels), ())),
		item_generator_script_language=hou.scriptLanguage.Python,
		default_value= int('0110111'[::-1], 2),
		),
	)

def _build_hda_network(parent: hou.Node) -> None:
	tmp_node = parent.createNode('null')
	tmp_node.setInput(0, parent.indirectInputs()[0])
	
	output_node = parent.createNode('output')
	output_node.setInput(0, tmp_node)
	
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

	parms = _build_parms()
	parm_template_group = hou.ParmTemplateGroup(parms)

	definition.setParmTemplateGroup(parm_template_group)
	hda_node.parm('channels').set(15)

	_build_hda_network(hda_node)
	definition.updateFromNode(hda_node)


if __name__ == '__main__':
	build()
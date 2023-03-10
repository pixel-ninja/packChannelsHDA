import os
import math

import hou

_COMPONENT_LETTERS = 'xyzw'

def findNextPowerOf2(n: int) -> int:
	k = 1
	while k < n:
		k = k << 1
	
	return k


def getAttribNames(geo: hou.Geometry, class_mode: int):
	'''Returns the list of point or vertex attribute names in geo.'''
	if class_mode == 0:
		return [ x.name() for x in geo.pointAttribs() ]
	else:
		return [ x.name() for x in geo.vertexAttribs() ]


def validSelectedAttributes(node: hou.Node) -> list[str]:
	'''Validate, update and return the list of attributes in the attributes parm.'''
	geo = node.input(0).geometry()

	class_mode = node.evalParm('class')
	attrs_parm = node.parm('attributes')
	attrs = attrs_parm.eval()

	result = attrs.split(' ')
	if not ''.join(result).replace(' ', ''):
		result = []

	# Get attrib names
	valid_attrs = getAttribNames(geo, class_mode)

	# Filter out invalid attribute names
	result[:] = [x for x in result if x in valid_attrs]

	# Update parm if value changed
	result_string = ' '.join(result)
	if result_string != attrs:
		attrs_parm.set(result_string)	

	return result


def calculateOutputSize(node: hou.Node) -> tuple[int, int, int]:
	'''
	Calculate the minimum texture size for the given geometry and attributes.
	Width will be rounded up to the nearest power of 2.
	Height can either be smallest or nearest power of 2.

	Returns tuple containing width, height and min_height.
	Also sets these in the output_size parm.
	'''
	geo = node.input(0).geometry()

	class_mode = node.evalParm('class')
	num_elements = geo.intrinsicValue('vertexcount' if class_mode else 'pointcount')
	num_attrs = node.evalParm('texture_multiparm')
	
	force_square = node.evalParm('height')
	square = findNextPowerOf2(int(math.sqrt(num_elements * num_attrs)))
	square = max(square, findNextPowerOf2(int(math.ceil(num_elements / square) * num_attrs)))
	
	width = square
	min_height = math.ceil(num_elements / square) * num_attrs
	height = square if force_square else min_height 
	
	node.parmTuple('output_size').set((width, height, min_height))
	return width, height, num_attrs


def evalTextureMultiParm(node: hou.Node) -> list[tuple[str, int]]:
	result = []
	multiparm = node.parm('texture_multiparm')
	multiparm_instances = multiparm.multiParmInstances()
	for parm in multiparm_instances:
		value = parm.evalAsString()

		# Skip folders
		if value == '0':
			continue

		# Extract name and component
		mapping = value.split('.')
		name = mapping[0]

		# Convert single space to None
		# Single space required for blank menu option
		if name == ' ':
			name = None

		if len(mapping) > 1:
			# Get component number (convert from xywz if required)
			component = mapping[1]
			component = _COMPONENT_LETTERS.index(component) if component in _COMPONENT_LETTERS else int(component)
		else:
			# Handle single component attributes
			component = 0

		result.append((name, component))
	
	return result


def attributeValueDict(geo: hou.Geometry, class_mode: int, attrib_names: list[str]) -> dict[str, list[float]]:
	if class_mode == 0:
		return { x: geo.pointFloatAttribValues(x) for x in attrib_names if x is not None }
	else:
		return { x: geo.vertexFloatAttribValues(x) for x in attrib_names if x is not None }
	

def attributeSizeDict(geo: hou.Geometry, class_mode: int, attrib_names: list[str]) -> dict[str, int]:
	if class_mode == 0:
		return { x: geo.findPointAttrib(x).size() for x in attrib_names if x is not None }
	else:
		return { x: geo.findVertexAttrib(x).size() for x in attrib_names if x is not None }


def componentValueDict(
	geo: hou.Geometry,
	class_mode: int,
	attrib_mapping: list[tuple[str, int]],
	) -> dict[tuple[str, int],list[float]]:

	unique_attribs = { x[0] for x in attrib_mapping }
	unique_components = set(attrib_mapping)
	attrib_sizes = attributeSizeDict(geo, class_mode, unique_attribs)
	attrib_values = attributeValueDict(geo, class_mode, unique_attribs)

	result = {}

	for (name, component) in unique_components:
		if (name, component) in result:
			continue

		if name is None:
			continue

		result[(name, component)] = attrib_values[name][component::attrib_sizes[name]]

	return result


def pixelValues(
	attribute_mapping: list[tuple[str, int]],
	component_values: dict[tuple[str, int],list[float]],
	width: int,
	height: int,
	min_height: int,
	num_elements: int
	) -> list[float]:
	'''
	Returns a list of floats, with every 4 values corresponding to a single rgba pixel value.
	Each row (set of 4 component values) is mapped sequentially by point/vertex number.
	Rows are then evenly spaced within the list.
	'''


	result = [0.0, 0.0, 0.0, 1.0] * width * height

	# row_span = math.ceil(num_elements / width) * width * 4  # Min row span
	row_span = int(math.ceil(height / (len(attribute_mapping) / 4)) * width * 4)  # Evenly spaced

	for i, (name, component) in enumerate(attribute_mapping):
		if name is None:
			continue

		row = int(math.floor(i / 4))
		start = i % 4 + row * row_span
		end = start + num_elements * 4
		result[start:end:4] = component_values[(name, component)]

	return result


def saveTexture() -> None:
	'''Write data texture with selected component values.'''

	node = hou.pwd()
	geo = node.input(0).geometry()
	path = node.evalParm('output')
	class_mode = node.evalParm('class')
	num_elements = geo.intrinsicValue('vertexcount' if class_mode else 'pointcount')
	valid_attrs = validSelectedAttributes(node)
	
	# Get image size
	width, height, min_height = node.evalParmTuple('output_size')
	print(f'Output size: {width} x {height}')
	

	# Get pixel component values from multiparm settings
	print('Getting attribute values')
	attribute_mapping = evalTextureMultiParm(node)
	component_values = componentValueDict(geo, class_mode, attribute_mapping)
	pixel_values = pixelValues(attribute_mapping, component_values, width, height, min_height, num_elements )
	
	# Save Image
	# attrs_string = '-'.join(attrs)
	# path = path.replace('{attrs}', attrs_string) 
	print(f'Saving to: {path}')
	
	# Make Folders if they don't exist
	folder = os.path.dirname(path)
	if not os.path.exists(folder):
		os.makedirs(folder)
	
	hou.saveImageDataToFile(pixel_values, width, height, path)
	print('Done')


# UI and Menu Functions

def toggle_attributes(kwargs: dict) -> None:
	'''Display options only for selected attribute buttons.'''
	node = kwargs['node']
	channelsParm = node.parm('channels')
	channelNames = channelsParm.menuLabels()
	channels = node.evalParm('channels')
	channels = format(channels, f'0{len(channelNames)}b')[::-1]
	
	for i, name in enumerate(channelNames):
		node.parm(name).hide(channels[i] == '0')


def attribute_menu_list(kwargs: dict) -> list[str]:
	'''Returns a list of point or vertex attributes for the input geometry.'''
	node = kwargs['node']

	if not node.inputs():
		return []
	
	geo = node.inputs()[0].geometry()
	class_mode = node.evalParm('class')
	result = getAttribNames(geo, class_mode) * 2
	result.sort()
	
	return result


def component_menu_list(kwargs: dict) -> list[str]:
	'''Returns token,label paired list of all point attribute components.'''
	node = kwargs['node']
	parm = kwargs['parm']

	if not node.inputs():
		return []
	
	class_mode = node.evalParm('class')
	geo = node.input(0).geometry()
	attribs = geo.vertexAttribs() if class_mode else geo.pointAttribs()
	attrib_names = node.evalParm('attributes').split(' ')

	attribs = [geo.findVertexAttrib(x) if class_mode else geo.findPointAttrib(x) for x in attrib_names]

	result = []
	for attrib in attribs:
		if not attrib:
			continue
		
		if attrib.dataType() not in [hou.attribData.Float, hou.attribData.Int]:
			continue
			
		name = attrib.name()
		size = attrib.size()
		
		if size == 1:
			result.append(name)
		elif size < 5:
			for i in range(size):
				result.append(f'{name}.{_COMPONENT_LETTERS[i]}')
		else:
			for i in range(size):
				result.append(f'{name}.[{i}]')

	result = sorted(result * 2)  # Duplicate entries for expected token-label pairs
	result = [' '] * 2 + result  # Prepend blank default value
	
	return result

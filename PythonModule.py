import os
import math

def findNextPowerOf2(n: int) -> int:
	k = 1
	while k < n:
		k = k << 1
	
	return k


def validSelectedAttributes() -> list[str]:
	attrs = hou.pwd().evalParm('attributes').split(' ')
	if not ''.join(attrs):
		attrs = []

	return attrs

def calculateOutputSize():
	node = hou.pwd()
	geo = node.geometry()
	valid_attrs = validSelectedAttributes()
		
	class_mode = hou.pwd().evalParm('class')
	num_elements = geo.intrinsicValue('vertexcount' if class_mode else 'pointcount')
	num_attrs = len(valid_attrs) # int(len(data)/4/width)  # Number of attrs
	
	square = findNextPowerOf2(math.sqrt(num_elements * num_attrs))
	width = square
	height = math.ceil(num_elements / width) * num_attrs 
	
	node.parmTuple('output_size').set((width, height, num_attrs))
	return width, height, num_attrs

def saveTexture():
	node = hou.pwd()
	geo = node.geometry()
	path = node.evalParm('output')
	valid_attrs = validSelectedAttributes()
	
	# Get image size
	width, height, num_attrs = node.evalParmTuple('output_size')
	print(f'Output size: {width} x {height}')
		
	# Get list of all attributes as vec4s
	data, attrs = getAttribsAsVec4(geo, width, valid_attrs)
	
	# Save Image
	attrs_string = '-'.join(attrs)
	path = path.replace('{attrs}', attrs_string) 
	print(f'Saving to: {path}')
	
	# Make Folders if they don't exist
	folder = os.path.dirname(path)
	if not os.path.exists(folder):
		os.makedirs(folder)
	
	# hou.saveImageDataToFile(data, width, height, path)
	print('Done')
	
	
def padVec3ListToVec4(inList, value):
	'''Mutates flattened float list from vec3 to vec4'''
	i = 3
	while i < len(inList)+1:
		inList.insert(i, value)
		i += 4

def getAttribsAsVec4(geo, width, valid_attrs=[]):
	'''Returns flattened float list of all vertex attrs'''
	data = []
	attrs = []
	
	class_mode = hou.pwd().evalParm('class')
	attribs = list(geo.vertexAttribs() if class_mode else geo.pointAttribs())
	attribs.sort(key=lambda x: x.name().lower())

	for attrib in attribs:
		name = attrib.name()
		if valid_attrs and name not in valid_attrs:
			continue
		
		attrs.append(name)
		print("Getting: " + name)

		values = list(geo.vertexFloatAttribValues(name) if class_mode else geo.pointFloatAttribValues(name))

		if attrib.size() == 3:
			padVec3ListToVec4(values, 1)
		
			
		# Extend values to next multiple of image width
		pad_amount = ((width * 4) - len(values)) % (width * 4)
		values.extend([0] * pad_amount)
		
		data.extend(values)

	return (data, attrs)

def toggle_attributes(kwargs: dict) -> None:
	node = kwargs['node']
	channelsParm = node.parm('channels')
	channelNames = channelsParm.menuLabels()
	channels = node.evalParm('channels')
	channels = format(channels, f'0{len(channelNames)}b')[::-1]
	
	for i, name in enumerate(channelNames):
		node.parm(name).hide(channels[i] == '0')


def attribute_menu_list(kwargs: dict) -> list[str]:
	node = kwargs['node']

	if not node.inputs():
		return []
	
	geo = node.inputs()[0].geometry()
	class_mode = node.evalParm('class')
	attrs = geo.vertexAttribs() if class_mode else geo.pointAttribs()
	
	result = []

	for attr in attrs:
		result.append(attr.name())
		result.append(attr.name())
	return result


def component_menu_list(kwargs: dict) -> list[str]:
	'''Returns token-label paired list of all point attribute components.'''
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
				result.append(f'{name}.{"xyzw"[i]}')
		else:
			for i in range(size):
				result.append(f'{name}.[{i}]')

	result = sorted(result * 2)  # Duplicate entries for expected token-label pairs
	result = [' '] * 2 + result  # Prepend blank default value
	
	return result
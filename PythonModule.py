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
	mode = node.evalParm('mode')
	attrs = geo.vertexAttribs() if mode else geo.pointAttribs()
	
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
	
	mode = node.evalParm('mode')
	geo = node.input(0).geometry()
	attribs = geo.vertexAttribs() if mode else geo.pointAttribs()
	attrib_names = node.evalParm('attributes').split(' ')

	attribs = [geo.findVertexAttrib(x) if mode else geo.findPointAttrib(x) for x in attrib_names]

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
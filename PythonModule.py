def toggleAttributes(kwargs: dict) -> None:
	node = kwargs['node']
	channelsParm = node.parm('channels')
	channelNames = channelsParm.menuLabels()
	channels = node.evalParm('channels')
	channels = format(channels, f'0{len(channelNames)}b')[::-1]
	
	for i, name in enumerate(channelNames):
		node.parm(name).hide(channels[i] == '0')
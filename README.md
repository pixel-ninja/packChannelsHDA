# Pack Channels - Houdini Digital Asset
This hda helps simplify the process of storing attribute data to vertex channels or textures for use in realtime applications.

# Build
To build the hda yourself you can run packChannelsHDA.py with hython (a specialised python interpreter that is installed with houdini).

# Reason this exists
While working on a few realtime projects I found the need to store attributes for use in shaders.
Pivot caching, mograph/particle style effects, masking, etc.

I quickly ran into the limit of what I could easily (i.e. no bit packing) store in the vertex channels themselves.
FBX only supports 8 float2 uv channels, and if you need to use Unity's shadergraph that number is cut in half.

This lead me to writing a python sop to export data textures, wrangles to set uvs to easily access those textures and ultimately this HDA to nicely package it all together for future use.

Hopefully someone else out there can find some use for it too.
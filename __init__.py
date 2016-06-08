
bl_info = {
	"name": "Gist Loader",
	"author": "Takosuke",
	"version": (0, 1, 0),
	"blender": (2, 77, 0),
	"location": "Text Editor > Properties Panel",
	"description": "Load gist info and raw data.",
	"support": "COMMUNITY",
	"wiki_url": "",
	"category": "Text Editor"}

if "bpy" in locals():
	import imp
	imp.reload(gist_loader)
else:
	from . import gist_loader

import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty


def register():
	gist_loader.register()

	bpy.types.Scene.gist_uid_property = StringProperty(name = "Gist UID", description = "Github Gist User ID")
	bpy.types.Scene.gists = CollectionProperty(type = bpy.types.GistInfo)
	bpy.types.Scene.active_gist_index = IntProperty(name = "active_gist_index", description = "active_gist_index")

def unregister():
	del bpy.types.Scene.gist_uid_property
	del bpy.types.Scene.gists
	del bpy.types.Scene.active_gist_index

	gist_loader.unregister()

if __name__ == "__main__":
	register()

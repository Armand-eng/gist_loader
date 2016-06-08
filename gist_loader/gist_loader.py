import bpy
import collections
import json
import os
from bpy.props import StringProperty, IntProperty, BoolProperty
from urllib.request import urlopen

class GetGistsInfoButton(bpy.types.Operator):
	bl_idname = "scene.get_gists_info"
	bl_label = "Load gists data from user id."

	key_files = "files"
	key_desc = "description"
	key_filename = "filename"
	key_raw_url = "raw_url"

	def execute(self, context):
		user_id = context.scene.gist_uid_property

		if user_id:
			context.scene.active_gist_index = 0
			self.get_gists(context, user_id)
		else:
			bpy.ops.error.gist_loader('INVOKE_DEFAULT',message = "Please fill in User ID.")

		return{'FINISHED'}

	def get_gists(self, context, user_id):
		url = "https://api.github.com/users/" + user_id + "/gists"
		open_url = None
		try:
			open_url = urlopen(url)
			if not open_url: return
		except Exception as ex:
			bpy.ops.error.gist_loader('INVOKE_DEFAULT',message = "Can not found User.")
			return

		json_raw = open_url.read().decode('UTF-8')
		gists_data = json.loads(json_raw, object_pairs_hook=collections.OrderedDict)

		scn = context.scene
		for i in range(0, len(scn.gists)):
			scn.gists.remove(0)

		for i, gist_data in enumerate(gists_data):
			for file_data in gist_data[self.key_files].values():
				gist = scn.gists.add()
				gist.file_name = file_data[self.key_filename]
				gist.raw_url = file_data[self.key_raw_url]
				gist.desc = gist_data[self.key_desc]

class LoadGistsTextButton(bpy.types.Operator):
	bl_idname = "scene.load_gists"
	bl_label = "Load checked gists."

	def execute(self, context):
		self.create_text(context)

		return{'FINISHED'}

	def create_text(self, context):
		gists = context.scene.gists
		selected_gists = [gist for gist in gists if gist.toggle_load_file]

		if len(selected_gists) <= 0:
			bpy.ops.error.gist_loader('INVOKE_DEFAULT',message = "No items selected.")
			return

		for gist in selected_gists:

			file_name = gist.file_name
			raw_url = gist.raw_url

			raw = urlopen(raw_url).read().decode('UTF-8')
			new_text = bpy.data.texts.new(file_name)
			new_text.write(raw)

class GistInfo(bpy.types.PropertyGroup):
	toggle_load_file = BoolProperty(default=False)
	file_name = StringProperty()
	raw_url = StringProperty()
	desc = StringProperty()

class TEXT_UL_gistslots(bpy.types.UIList):
	text_exts = [".txt", ".yml", ".ini", ".md"]
	script_exts = [".py"]

	def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
		slot = item
		if slot:
			path, ext = os.path.splitext(slot.file_name)
			icon_file_name = 'FILE'
			if ext in self.text_exts:
				icon_file_name = 'FILE_TEXT'
			elif ext in self.script_exts:
				icon_file_name = 'FILE_SCRIPT'

			col_name = layout.column()
			col_name.label(text=slot.file_name, icon=icon_file_name)

			col_load = layout.column()
			col_load.alignment = 'RIGHT'
			col_load.prop(slot, "toggle_load_file", icon_only=True)
		else:
			layout.label(text="", translate=False, icon_value=icon)

	def filter_items(self, context, data, propname):
		gists = getattr(data, propname)
		helper_funcs = bpy.types.UI_UL_list
		flt_flags = []
		flt_neworder = []

		flt_flags = [self.bitflag_filter_item] * len(gists)
		# print(self.filter_name)

		for idx, gist in enumerate(gists):
			if self.filter_name not in gist.file_name and self.filter_name not in gist.desc:
				flt_flags[idx] &= ~self.bitflag_filter_item

		if self.use_filter_sort_alpha:
			flt_neworder = helper_funcs.sort_items_by_name(gists, "file_name")

		return flt_flags, flt_neworder

class TEXT_PT_gist_load(bpy.types.Panel):
	bl_idname = "TEXT_PT_gist_load"
	bl_label = "Gist Loader"
	bl_space_type = "TEXT_EDITOR"
	bl_region_type = "UI"
	bl_context = "object"

	def draw(self, context):
		layout = self.layout
		row = layout.row()
		scn = bpy.context.scene
		obj = context.object

		layout.prop(scn, "gist_uid_property")
		layout.operator("scene.get_gists_info", text='Get Gists Info')
		layout.template_list("TEXT_UL_gistslots", "", scn, "gists", scn, "active_gist_index", rows= 8)
		layout.label("Description")

		desc = ""
		if len(scn.gists) > 0:
			active_gist = scn.gists[scn.active_gist_index]
			desc = active_gist.desc

		box = layout.box()
		box.label(desc)

		layout.operator("scene.load_gists", text='Load Selected Gists')

class GistLoaderMessageOperator(bpy.types.Operator):
	bl_idname = "error.gist_loader"
	bl_label = "Message"
	type = StringProperty(default="Error")
	message = StringProperty()

	def execute(self, context):
		self.report({'INFO'}, self.message)
		print(self.message)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_popup(self, width=300, height=200)

	def draw(self, context):
		self.layout.label(text="", icon='ERROR')
		self.layout.label(text=self.message)

classes = [
	TEXT_UL_gistslots,
	TEXT_PT_gist_load,
	GetGistsInfoButton,
	LoadGistsTextButton,
	GistInfo,
	GistLoaderMessageOperator
]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)



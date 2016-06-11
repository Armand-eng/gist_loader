import bpy
import collections
import datetime
import json
import os
import requests
import time
import urllib
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.app.translations import pgettext, pgettext_iface

class GetGistsInfoButton(bpy.types.Operator):
    bl_idname = "scene.get_gists_info"
    bl_label = "Load gists data from user id."

    key_header_limit = "X-RateLimit-Limit"
    key_header_remaining = "X-RateLimit-Remaining"
    key_header_reset = "X-RateLimit-Reset"
    key_files = "files"
    key_desc = "description"
    key_filename = "filename"
    key_raw_url = "raw_url"
    key_url = "url"
    key_link = "link"
    key_last = "last"
    key_page = "page"

    url_param_page = "page"

    def execute(self, context):
        print("----- get gists info start " + datetime.datetime.now().strftime("%H:%M:%S") + " -----")

        requests.packages.urllib3.disable_warnings()
        user_id = context.scene.gist_loader_settings.user_id

        if user_id:
            context.scene.gist_loader_settings.active_gist_index = 0
            self.get_gists(context, user_id)
        else:
            bpy.ops.error.gist_loader('INVOKE_DEFAULT',message=pgettext_iface("Please fill in User ID."))

        print("----- get gists info end   " + datetime.datetime.now().strftime("%H:%M:%S") + " -----")

        return{'FINISHED'}

    def get_gists(self, context, user_id):
        settings = context.scene.gist_loader_settings
        max_page = context.user_preferences.addons[settings.addon_name].preferences.max_page
        url = "https://api.github.com/users/" + user_id + "/gists"

        if settings.end_page - settings.start_page + 1 > max_page:
            bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface("Please set a range of pages in max number of pages ({0}).").format(max_page))
            return

        proxies = self.get_proxies(context, settings)

        start_page = settings.start_page

        # 最初のページだけ取得し、ヘッダを調査
        params_start = {self.url_param_page: str(start_page)}
        request_start = requests.get(url, verify=False, params=params_start, proxies=proxies)
        print("page number : {0}".format(start_page))
        self.print_limit(request_start)

        if not request_start:
            if self.reach_limit(request_start):
                message = "Resquest limit reached. Reset : {0}"
                bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface(message).format(self.get_reset_time(request_start)))
            else:
                bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface("Can not found User."))
            return

        last_page = 1
        if self.key_link in request_start.headers:
            if self.key_last in request_start.links:
                last_url = request_start.links[self.key_last][self.key_url]
                splited_url = urllib.parse.urlsplit(last_url)
                query_raw = urllib.parse.parse_qs(splited_url.query)
                last_page = int(dict(query_raw)[self.key_page][0])
            else:
                # lastキーが無い場合、そのページが最終ページ
                last_page = start_page

        print("last page : {0}".format(last_page))

        gists_data_start = json.loads(request_start.text, object_pairs_hook=collections.OrderedDict)
        if not gists_data_start:
            if start_page == 1:
                bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface("This User has no gists."))
                return
            elif last_page < settings.start_page:
                bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface("The last page of this user is {0}.").format(last_page))
                settings.start_page = last_page
                settings.end_page = last_page
                return

        if last_page < settings.end_page:
            bpy.ops.error.gist_loader('INVOKE_DEFAULT', type="Message", message=pgettext_iface("The last page of this user is {0}.").format(last_page))
            settings.end_page = last_page

        end_page = settings.end_page

        for i in range(0, len(settings.gists)):
            settings.gists.remove(0)

        self.add_gist(settings.gists, gists_data_start)

        # 以降のページを取得
        for page_num in range(start_page + 1, end_page + 1):
            params = {self.url_param_page: str(start_page)}
            request = requests.get(url, params=params, verify=False, proxies=proxies)
            print("page number : {0}".format(page_num))
            self.print_limit(request)

            if not request:
                if self.reach_limit(request):
                    message = "Resquest limit reached. Reset : {0}"
                    bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface(message).format(self.get_reset_time(request)))
                else:
                    bpy.ops.error.gist_loader('INVOKE_DEFAULT', message=pgettext_iface("Can not found Page."))
                return

            gist_data = json.loads(request.text, object_pairs_hook=collections.OrderedDict)
            self.add_gist(settings.gists, gist_data)

    def get_proxies(self, context, settings):
        proxies = {}

        if context.user_preferences.addons[settings.addon_name].preferences.proxy and settings.use_proxy:
            protocol = settings.proxy_protocol
            address = settings.proxy_address
            port = settings.proxy_port
            proxies = { protocol: "http://" + address + ":" + port}

        return proxies

    def print_limit(self, request):
        limit = request.headers[self.key_header_limit]
        remaining = request.headers[self.key_header_remaining]

        print(self.key_header_limit + " : " + limit)
        print(self.key_header_remaining + " : " + remaining)
        print(self.key_header_reset + " : " + self.get_reset_time(request))

    def reach_limit(self, request):
        remaining = request.headers[self.key_header_remaining]
        return True if int(remaining) == 0 else False

    def get_reset_time(self, request):
        reset = request.headers[self.key_header_reset]
        time_raw = time.localtime(int(reset))
        return time.strftime("%H:%M:%S", time_raw)

    def add_gist(self, gists, gists_data):
        for i, gist_data in enumerate(gists_data):
            for file_data in gist_data[self.key_files].values():
                gist = gists.add()
                gist.file_name = file_data[self.key_filename]
                gist.raw_url = file_data[self.key_raw_url]
                desc = gist_data[self.key_desc]
                if desc != None:
                    gist.desc = gist_data[self.key_desc]

class LoadGistsTextButton(bpy.types.Operator):
    bl_idname = "scene.load_gists"
    bl_label = "Load checked gists."

    def execute(self, context):
        print("----- get gists text start " + datetime.datetime.now().strftime("%H:%M:%S") + " -----")
        self.create_text(context)
        print("----- get gists text end   " + datetime.datetime.now().strftime("%H:%M:%S") + " -----")

        return{'FINISHED'}

    def create_text(self, context):
        gists = context.scene.gist_loader_settings.gists
        selected_gists = [gist for gist in gists if gist.toggle_load_file]

        if len(selected_gists) <= 0:
            bpy.ops.error.gist_loader('INVOKE_DEFAULT',message=pgettext_iface("No items selected."))
            return

        open_text = None
        for gist in selected_gists:
            file_name = gist.file_name
            raw_url = gist.raw_url
            print(file_name + " : " + raw_url)

            request = requests.get(raw_url, verify=False)
            # print(request.headers)
            text = request.text
            new_text = bpy.data.texts.new(file_name)
            new_text.write(text)
            if not open_text:
                open_text = new_text

        text = bpy.data.texts["sample.py"]
        bpy.context.space_data.text = open_text

class GistInfo(bpy.types.PropertyGroup):
    toggle_load_file = BoolProperty(default=False)
    file_name = StringProperty()
    raw_url = StringProperty()
    desc = StringProperty()

class TEXT_UL_gistslots(bpy.types.UIList):
    text_exts = [".txt", ".yml", ".ini", ".md"]
    script_exts = [".py", ".osl"]

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
            col_name.label(text=slot.file_name, translate=False, icon=icon_file_name)

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
        settings = bpy.context.scene.gist_loader_settings
        use_translate_interface = context.user_preferences.system.use_translate_interface

        layout.prop(settings, "user_id")
        row = layout.row()
        row.label(pgettext_iface("Page:"))
        row.prop(settings, "start_page")
        row.prop(settings, "end_page")

        if context.user_preferences.addons[settings.addon_name].preferences.proxy:
            layout.prop(settings, "use_proxy")
            layout.prop(settings, "proxy_protocol")
            layout.prop(settings, "proxy_address")
            layout.prop(settings, "proxy_port")

        layout.operator("scene.get_gists_info", text=pgettext("Get Gists Info"))
        layout.template_list("TEXT_UL_gistslots", "", settings, "gists", settings, "active_gist_index", rows= 8)
        layout.label(pgettext_iface("Description: "))

        desc = ""
        if len(settings.gists) > 0:
            active_gist = settings.gists[settings.active_gist_index]
            desc = active_gist.desc

        box = layout.box()
        box.label(desc)

        layout.operator("scene.load_gists", text=pgettext("Load Selected Gists"))

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
        if self.type == "Message":
            self.layout.label(text="", icon='INFO')
        else:
            self.layout.label(text="", icon='ERROR')
        self.layout.label(text=self.message)


bl_info = {
    "name": "Gist Loader",
    "author": "Takosuke",
    "version": (0, 2, 0),
    "blender": (2, 77, 0),
    "location": "Text Editor > Properties Panel",
    "description": "Load gist info and raw data.",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Text"}

if "bpy" in locals():
    import imp
    imp.reload(gist_loader)
else:
    from . import gist_loader

import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty, BoolProperty, EnumProperty

class GistLoaderAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    proxy = BoolProperty(name="Proxy", default=False)
    max_page = IntProperty(name="Max number of pages", description="Max number of pages", default=10, min=10, max=100)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "proxy")
        layout.prop(self, "max_page")

class GistLoaderSettings(bpy.types.PropertyGroup):

    def start_page_update_event(self, context):
        settings = context.scene.gist_loader_settings
        if settings.start_page > settings.end_page:
            settings.end_page = settings.start_page

    def end_page_update_event(self, context):
        settings = context.scene.gist_loader_settings
        if settings.start_page > settings.end_page:
            settings.start_page = settings.end_page

    addon_name = StringProperty(name="Addon Name", description="Addon Name", default=__name__)
    user_id = StringProperty(name="User ID", description="Github Gist User ID")
    gists = CollectionProperty(type=gist_loader.GistInfo)
    start_page = IntProperty(name="Start", description="Start Page. 30 gists in a page.", default=1, min=1, max=100, update=start_page_update_event)
    end_page = IntProperty(name="End", description="End Page. 30 gists in a page.", default=1, min=1, max=100, update=end_page_update_event)
    active_gist_index = IntProperty(name="Active Gist Index", description="active gist index")
    use_proxy = BoolProperty(name="Use Proxy", description="Use Proxy", default=True)
    proxy_protocol = StringProperty(name="Protocol", description="Protocol", default="http")
    proxy_address = StringProperty(name="Address", description="Address")
    proxy_port = StringProperty(name="Port", description="Port", default="8080")

translations = {
    "ja_JP": {
        ("*", "User ID"): "ユーザーID",
        ("*", "Page:"): "ページ:",
        ("Operator", "Get Gists Info"): "Gist 情報を取得",
        ("*", "Description: "): "詳細:",
        ("Operator", "Load Selected Gists"): "選択したファイルを読み込む",
        ("*", "Use Proxy"): "プロキシを使う",
        ("*", "Protocol"): "プロトコル",
        ("*", "Address"): "アドレス",
        ("*", "Port"): "ポート",
        ("*", "Please fill in User ID."): "ユーザーIDを入力して下さい。",
        ("*", "Please set a range of pages in max number of pages ({0})."): "最大ページ数({0})の範囲内で設定して下さい。",
        ("*", "Can not found User."): "ユーザーが見つかりません。",
        ("*", "This User has no gists."): "指定したユーザーにはGistが存在しません。",
        ("*", "The last page of this user is {0}."): "指定したユーザーの最終ページは{0}です。",
        ("*", "No items selected."): "アイテムが選択されていません。",
    }
}

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.gist_loader_settings = bpy.props.PointerProperty(type=GistLoaderSettings)
    bpy.app.translations.register(__name__, translations)

def unregister():
    bpy.app.translations.unregister(__name__)
    del bpy.types.Scene.gist_loader_settings
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

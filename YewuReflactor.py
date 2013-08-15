# encoding: utf-8
import sublime, sublime_plugin

class ReflactYewuPage(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view

        #add MasterPageFile attribute to <%@ Page ..>
        v.run_command("add_attribute", {'tag':"%@ Page", 'add_attributes':{"MasterPageFile": "../Default.Master"}})

        v.run_command("delete_tag", {"tag": "!DOCTYPE"})

        #delete <html> tag but leave innerHTML
        v.run_command("delete_wrap_tag", {"tag": "html"})

        #replace <head> tag with <asp:Content>
        v.run_command("replace_tag", {"tag": "head", "new_tag": "asp:Content",
             "new_tag_attr": {"ID":"Header1", "ContentPlaceHolderID":"HeadPlace", "runat":"server"}})

        #remove tag which are presented in master page
        v.run_command("delete_tag", {"tag": "title"})
        v.run_command("delete_tag", {"tag": "link", "conditions": {"href": ".*/admin.css"}})
        v.run_command("delete_tag", {"tag": "link", "conditions": {"href": ".*/jq_ui.custom.css"}})

        v.run_command("delete_tag", {"tag": "script", "conditions": {"src": ".*/jquery.js"}})
        v.run_command("delete_tag", {"tag": "script", "conditions": {"src": ".*/common.js"}})
        v.run_command("delete_tag", {"tag": "script", "conditions": {"src": ".*/popup.js"}})
        v.run_command("delete_tag", {"tag": "script", "conditions": {"src": ".*/popup_helper.js"}})
        v.run_command("delete_tag", {"tag": "script", "conditions": {"src": ".*/jq_ui.custom.js"}})
        v.run_command("delete_tag", {"tag": "script", "conditions": {"src": ".*datepicker-zh-CN.js"}})


        #remove all of type attributes from <script>
        v.run_command("remove_attribute", {"tag": "script", "attribute": "type"})
        v.run_command("remove_attribute", {"tag": "script", "attribute": "language"})

        v.run_command("append_to_tag", {"tag": "script", "to_tag": "body"})

        #replace <body> tag with <asp:Content>
        v.run_command("replace_tag", {"tag": "body", "new_tag": "asp:Content",
             "new_tag_attr": {"ID":"Content1", "ContentPlaceHolderID":"ContentPlace", "runat":"server"}})


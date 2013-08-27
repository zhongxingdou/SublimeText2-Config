# encoding: utf-8
import sublime, sublime_plugin
import HtmlReflactor
import re

class ReflactUseMasterPage(sublime_plugin.TextCommand):
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
        # v.run_command("delete_tag", {"tag": "title"})
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


class ReflactInputServerControl(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view

        #repace ID, CssClass
        tb_tag = "asp:(TextBox|HiddenField)"
        tb_regions = HtmlReflactor.find_tags_with_attribute(v, tb_tag)
        offset = 0
        for region in tb_regions:
            tb_region = HtmlReflactor.offset_region(region, offset)
            tb_tag = v.substr(tb_region)
            tb_tag = HtmlReflactor.replace_attr_name(tb_tag, {"ID": "id", "CssClass": "class"})

            v.replace(edit, tb_region, tb_tag)
            offset += len(tb_tag) - tb_region.size() 


        # replace TagName
        HtmlReflactor.replace_text(v, "<asp:TextBox ", '<input type="text" ')
        HtmlReflactor.erase_text(v, "</asp:TextBox>")
        HtmlReflactor.replace_text(v, "<asp:HiddenField ", '<input type="hidden" ')

        # text_input_regions = HtmlReflactor.find_tags_with_attribute(v, "input", {"runat": "server", "type": "(?:text|hidden)"})
        text_input_regions = HtmlReflactor.find_tags_with_attribute(v, "input", {"runat": "server"})
        offset = 0
        for region in text_input_regions:
            tag_region = HtmlReflactor.offset_region(region, offset)
            tag = v.substr(tag_region)
            print tag
            matches = re.search(r"id=([\"'])(?P<id>.*?)\1", tag)
            if matches:
                id_attr = matches.group("id")

                model_field = re.search(r"^(?P<model>.*)_(?P<field>.*?)$", id_attr)
                if model_field:
                    model = model_field.group("model")
                    field = model_field.group("field")
                else:
                    model = "Model"
                    field = id_attr

                value = "Curr" + model.replace("_", "") + "." + field
                runat_region = v.find("runat=([\"'])server\\1", tag_region.a, sublime.IGNORECASE)
                if runat_region:
                    v.erase(edit, runat_region)
                    offset -= runat_region.b - runat_region.a

                content = ' name="%s" value="<%%= %s %%>"' % (id_attr, value)
                v.insert(edit, tag_region.a + 6, content)
                offset += len(content)

                
                # v.run_command("remove_attribute", {"tag": "input", "attribute": "runat", "value": "server"})
class ReflactButtonServerControl(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view
        btn_tag = "asp:Button"

        # v.run_command("remove_attribute", {"tag": btn_tag, "attribute": "runat"})

        btn_regions = HtmlReflactor.find_tags_with_attribute(v, btn_tag)

        offset = 0
        for region in btn_regions:
            btn_region = HtmlReflactor.offset_region(region, offset)
            btn_tag = v.substr(btn_region)

            btn_tag = btn_tag.replace("asp:Button", 'input type="submit" name="action"')
            btn_tag = HtmlReflactor.remove_attribute(btn_tag, "onclick")
            btn_tag = HtmlReflactor.remove_attribute(btn_tag, "runat")
            btn_tag = HtmlReflactor.replace_attr_name(btn_tag, {"ID": "id", "CssClass": "class", "OnClientClick": "onclick", "Text": "value"})
            
            v.replace(edit, btn_region, btn_tag)

            offset += len(btn_tag) - (btn_region.b - btn_region.a)


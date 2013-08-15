# encoding: utf-8
import sublime, sublime_plugin
import re

#注意 sublime的view.find_all(pattern, ...) pattern应该是perl正则式，而不是python的，所以不支持python的特殊
#写法，如?P<GroupName> ?P=GroupName，可用\1\2代替

def is_self_closing_tag(tag):
    return tag.lower() in ["area", "base", "basefont", "br", "hr", "input", "img", "link", "meta"]

def offset_region(region, offset):
    return sublime.Region(region.a + offset, region.b + offset)

def find_end_region(view, tag, from_position):
    start_re = "<" + tag + "(?:>| [^>]*>)"
    end_re = "</" + tag + ">"
    e_region = view.find(end_re, from_position, sublime.IGNORECASE)
    if(e_region == None):
        return None
    else:
        s_region = view.find(start_re, from_position, sublime.IGNORECASE)
        if(s_region == None):
            return e_region
        elif(e_region.a < s_region.a):
            return e_region
        else:
            sub_e_region = find_end_region(view, tag, s_region.b)
            return find_end_region(view, tag, sub_e_region.b)

def find_tags_with_attribute(view, tag, conditions):
    if conditions:
        # regexp = "<" + tag + " [^>]*"
        regexp = "<" + tag + " "

        i = 1
        for attr, value in conditions.items():
            if value != None:
                regexp += "(?=.*" + attr + "=(['" + '"]?)' + value + "\\" + str(i) + ")"
                # regexp += "(?=.*" + attr + "=(?P<q" + str(i) + ">['" + '"]?)' + value + "(?P=q" + str(i) + "))"
                i += 1
            else:
                regexp += "(?!" + attr + "=)"           

        regexp += "[^>]*?>"
    else:
        regexp = "<" + tag + "(?:>| [^>]*?>)"
    print regexp
    return view.find_all(regexp, sublime.IGNORECASE)

# v.run_command("replace_tag", {"tag": "head", "new_tag": "asp:Content", "new_tag_attr": {"ID":"Content1", "ContentPlaceHolderID":"HeadPlace", "runat":"server"}})
class ReplaceTagCommand(sublime_plugin.TextCommand):
    def run(self, edit, tag, new_tag, new_tag_attr=None, conditions={}):
        view = self.view

        attrs = ""
        if new_tag_attr:
            for key, value in new_tag_attr.items():
                attrs += " " + key + '="' + value + '"'

        start_text = "<" + new_tag + attrs + ">"
        end_text =  "</" + new_tag + ">"

        regions = find_tags_with_attribute(view, tag, conditions)
        region_offset = 0
        for region in regions:
            real_region = offset_region(region, region_offset)
            # print "start region:"
            # print region
            closing_tag = find_end_region(view, tag, real_region.b)
            if(closing_tag):
                # print "close region:"
                # print closing_tag
                view.replace(edit, real_region, start_text)
                offset = len(start_text) - (region.b - region.a)
                region_offset += offset

                real_closing_tag = offset_region(closing_tag, offset)
                view.replace(edit, real_closing_tag, end_text)

                region_offset = region_offset - (closing_tag.b - closing_tag.a) + len(end_text)
                # print region_offset
            else:
                print "!!! can't find out closing tag"



# v.run_command("add_attribute", {'tag':"%@ Page", 'add_attributes':{"MasterPageFile": "../Default.Master"}})
class AddAttribute(sublime_plugin.TextCommand):
    def run(self, edit, tag, add_attributes, conditions={}):
        view = self.view

        insert_attr = ""
        for key, value in add_attributes.items():
            insert_attr += " " + key + '="' + value + '"'
            conditions[key] = None

        offset = 0
        tag_len = len(tag)
        attr_len = len(insert_attr)

        regions = find_tags_with_attribute(view, tag, conditions)
        for region in regions:
            insert_pos = region.a + offset + tag_len + 1
            # print insert_pos
            view.insert(edit, insert_pos, insert_attr)
            offset += attr_len

# v.run_command("delete_wrap_tag", {"tag": "html"})
class DeleteWrapTag(sublime_plugin.TextCommand):
    def run(self, edit, tag, conditions={}):
        view = self.view
        regions = find_tags_with_attribute(view, tag, conditions)
        clear_count = 0
        for region in regions:
            start_region = offset_region(region, clear_count)
            closing_region = find_end_region(view, tag, start_region.b)
            # print start_region
            # print closing_region
            if closing_region:
                # remove start tag
                view.erase(edit, start_region)
                start_len = region.b - region.a
                clear_count -= start_len

                # remove closing  tag
                view.erase(edit, offset_region(closing_region, -start_len))
                clear_count -= closing_region.b - closing_region.a

class DeleteTag(sublime_plugin.TextCommand):
    def run(self, edit, tag, conditions={}):
        view = self.view

        regions = find_tags_with_attribute(view, tag, conditions)
        clear_count = 0
        if is_self_closing_tag(tag):
            for region in regions:
                view.erase(edit, offset_region(region, clear_count))
                clear_count -= region.b - region.a
        else:
            for region in regions:
                start_region = offset_region(region, clear_count)
                end_region = find_end_region(view, tag, start_region.b)
                if end_region:
                    view.erase(edit, sublime.Region(start_region.a, end_region.b))
                    clear_count -= end_region.b - start_region.a
                else: #比如<!DOCTYPE ...>
                    view.erase(edit, start_region)
                    clear_count -= start_region.b - start_region.a


# v.run_command("remove_attribute", {"tag": "script", "attribute": "type"})
class RemoveAttribute(sublime_plugin.TextCommand):
    def run(self, edit, tag, attribute, value="[^>]*"):
        view = self.view
        regions = find_tags_with_attribute(view, tag, {attribute: value})
        clear_count = 0
        for region in regions:
            new_region = sublime.Region(region.a - clear_count, region.b - clear_count)
            content = view.substr(new_region)
            pattern = re.compile(" ?" + attribute+"=['\"]"+value+"?['\"]")
            m=pattern.search(content)
            if m:
                # print content
                p1 = new_region.a + m.start()
                p2 = new_region.a + m.end()
                clear_count += (p2 - p1)
                view.erase(edit, sublime.Region(p1, p2))


# v.run_command("append_tag", {"tag": "body", "new_tag": "js"})
class AppendTag(sublime_plugin.TextCommand):
    def run(self, edit, tag, new_tag, new_tag_attr=None, conditions={}):
        view = self.view
        regions = find_tags_with_attribute(view, tag, conditions)

        attrs = ""
        if new_tag_attr:
            for key, value in new_tag_attr.items():
                attrs += " " + key + '="' + value + '"'

        if is_self_closing_tag(new_tag):
            insert_tag = "<" + new_tag + attrs + "/>\n"
        else:
            insert_tag = "<" + new_tag + attrs + ">\n</" + new_tag + ">\n"

        insert_len = len(insert_tag)

        insert_count = 0
        for region in regions:
            end_region = find_end_region(view, tag, region.b + insert_count)
            if end_region:
                view.insert(edit, end_region.a, insert_tag)
                insert_count += insert_len


# v.run_command("append_to_tag", {"tag": "script", "to_tag": "js"})
class AppendToTag(sublime_plugin.TextCommand):
    def run(self, edit, tag, to_tag, tag_conditions={}, to_tag_conditions={}):
        view = self.view

        regions = find_tags_with_attribute(view, tag, tag_conditions)
        contents = []

        #collect contents
        solo_tag = is_self_closing_tag(tag)
        for region in regions:
            if solo_tag:
                contents.append(view.substr(region))
            else:
                end_region = find_end_region(view, tag, region.b)
                if end_region:
                    contents.append(view.substr(sublime.Region(region.a, end_region.b)))

        view.run_command("delete_tag", {"tag":tag, "conditions": tag_conditions})

        target = find_tags_with_attribute(view, to_tag, to_tag_conditions)[0]
        if target:
            target_end = find_end_region(view, to_tag, target.b)
            if target_end:
                view.insert(edit, target_end.a - 1, "\n"+"\n".join(contents))

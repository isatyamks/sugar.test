# Copyright 2009 Simon Schampijer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""HelloWorld Activity: A case study for developing an activity."""

import gi
import logging
import json
import time
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject

from gettext import gettext as _

from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics import style

# --- AI Reflection Components ---

class ReflectionService(object):
    """
    Service to handle AI reflection logic.
    Mocks the interaction with an external LLM service.
    """
    def __init__(self):
        pass

    def get_reflection_prompt(self, callback):
        """
        Mock function to get a reflection prompt from AI.
        """
        logging.debug('ReflectionService: Requesting prompt...')
        # Simulate network delay
        GLib.timeout_add_seconds(1, self._mock_api_response, callback)

    def _mock_api_response(self, callback):
        # Default prompt for testing
        prompt = "You've been working hard! What is one thing you learned while using this activity today?"
        logging.debug('ReflectionService: Generated prompt: %s', prompt)
        callback(prompt)
        return False

class ReflectionDialog(Gtk.Window):
    """
    Dialog to display AI prompt and collect user reflection.
    """
    def __init__(self, parent_window, question, callback):
        Gtk.Window.__init__(self)
        self.set_modal(True)
        self.set_transient_for(parent_window)
        self.set_default_size(600, 400)
        self.set_border_width(style.DEFAULT_SPACING * 2)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_title(_('Reflection Time'))
        
        self.question = question
        self.callback = callback
        
        vbox = Gtk.VBox(spacing=style.DEFAULT_SPACING)
        self.add(vbox)
        
        # Title
        label_title = Gtk.Label()
        label_title.set_markup("<span size='x-large' weight='bold'>{}</span>".format(_('Reflection Time')))
        vbox.pack_start(label_title, False, False, 0)
        
        # Question
        label_question = Gtk.Label()
        label_question.set_markup("<span>{}</span>".format(question))
        label_question.set_line_wrap(True)
        vbox.pack_start(label_question, False, False, style.DEFAULT_SPACING)
        
        # Answer
        self.answer_entry = Gtk.TextView()
        self.answer_entry.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.answer_entry)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        # Buttons
        bbox = Gtk.HButtonBox()
        bbox.set_layout(Gtk.ButtonBoxStyle.END)
        vbox.pack_start(bbox, False, False, 0)
        
        btn_skip = Gtk.Button(label=_("Skip"))
        btn_skip.connect('clicked', self._on_skip)
        bbox.add(btn_skip)
        
        btn_save = Gtk.Button(label=_("Save Reflection"))
        # Make the save button distinct
        btn_save.props.image = Gtk.Image.new_from_icon_name('document-save', Gtk.IconSize.BUTTON)
        btn_save.props.always_show_image = True
        btn_save.connect('clicked', self._on_save)
        bbox.add(btn_save)
        
        self.show_all()

    def _on_save(self, widget):
        buffer = self.answer_entry.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True)
        self.callback(text)
        self.destroy()

    def _on_skip(self, widget):
        self.callback(None)
        self.destroy()

# --- End AI Reflection Components ---

class HelloWorldActivity(activity.Activity):
    """HelloWorldActivity class as specified in activity.info"""

    def __init__(self, handle):
        """Set up the HelloWorld activity."""
        activity.Activity.__init__(self, handle)

        # Reflection state
        self._reflection_complete = False
        self._reflection_service = ReflectionService()

        # we do not have collaboration features
        self.max_participants = 1

        # toolbar
        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.connect('clicked', self._on_stop_clicked)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        # content
        label = Gtk.Label(_("Test Activity for AI Reflection"))
        self.set_canvas(label)
        label.show()

    def _on_stop_clicked(self, button):
        # Intercept the stop button to show reflection
        self.close()

    def close(self, skip_save=False):
        if self._reflection_complete or skip_save:
            logging.debug("HelloWorldActivity: Closing...")
            activity.Activity.close(self, skip_save=skip_save)
            return

        logging.debug("HelloWorldActivity: Intercepting close for reflection.")
        # Trigger reflection process
        self._reflection_service.get_reflection_prompt(self._show_reflection_ui)
        # return without calling super().close() to keep window open
        return

    def _show_reflection_ui(self, prompt):
        dialog = ReflectionDialog(self, prompt, self._on_reflection_response)
        dialog.show()

    def _on_reflection_response(self, answer):
        if answer:
            logging.debug("HelloWorldActivity: Saving reflection answer.")
            # Save reflection to metadata
            # We use the activity's metadata dictionary
            if self.metadata:
                # Append to description or custom field
                description = self.metadata.get('description', '')
                if description:
                    description += '\n\n'
                description += "--- Reflection ---\n" + answer
                self.metadata['description'] = description
                
                # We could also save structured data if needed
                self.save() # Trigger save before closing

        self._reflection_complete = True
        self.close()
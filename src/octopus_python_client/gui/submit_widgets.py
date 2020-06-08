import logging
import threading
import tkinter as tk
from tkinter import messagebox

from octopus_python_client.actions import Actions, ACTIONS_DICT
from octopus_python_client.common import Common, item_type_channels, project_id_key, name_key, id_key, \
    item_type_projects
from octopus_python_client.gui.common_widgets import CommonWidgets
from octopus_python_client.item_types import Constants
from octopus_python_client.migration import Migration
from octopus_python_client.release_deployment import ReleaseDeployment
from octopus_python_client.utilities.helper import find_item

logger = logging.getLogger(__name__)


class SubmitWidgets(tk.Frame):
    DIVIDER_BAR = "|"

    def __init__(self, parent: tk.Frame, server: Common, source: Common, next_button: tk.Button = None,
                 submit_button: tk.Button = None):
        super().__init__(parent)
        self.server = server
        self.source = source

        self.next_button = next_button
        self.submit_button = submit_button

        self.channel_id_var = None
        self.item_id_name_var = None
        self.new_item_name_var = None
        self.new_name_entry = None
        self.overwrite_var = None
        self.release_notes_var = None
        self.release_version_var = None

        self.update_step()

    def update_step(self):
        tk.Label(self, text=f"{self.server.config.action} ({ACTIONS_DICT.get(self.server.config.action)})",
                 bd=2, relief="groove").grid(sticky=tk.W)
        if self.server.config.action == Actions.ACTION_CREATE_RELEASE:
            self.set_create_release_frame()
        elif self.server.config.action == Actions.ACTION_CLONE_SPACE_ITEM:
            items_list = self.source.get_list_from_one_type(self.server.config.type)
            self.set_clone_item_frame(items_list=items_list)
        elif self.server.config.action == Actions.ACTION_CLONE_PROJECT_RELATED:
            if not self.server.config.project_ids:
                messagebox.showerror(title=f"No project selected", message=f"No destination project was selected!")
                self.submit_button.config(state=tk.DISABLED)
                return
            items_list = self.source.get_list_items_by_conditional_id(
                item_type=self.server.config.type, condition_key=project_id_key,
                condition_id=self.source.config.project_id)
            self.set_clone_item_frame(items_list=items_list)
        elif self.server.config.action == Actions.ACTION_CLONE_SPACE:
            self.set_clone_space_frame()
        else:
            self.submit_button.config(state=tk.DISABLED)

    def set_create_release_frame(self):
        self.set_radio_channels_frame()

        tk.Label(self, text="Release version number: ").grid(sticky=tk.W)
        self.release_version_var = tk.StringVar()
        self.release_version_var.set(self.server.config.release_version)
        tk.Entry(self, width=20, textvariable=self.release_version_var).grid(sticky=tk.W)

        tk.Label(self, text="Release notes: ").grid(sticky=tk.W)
        self.release_notes_var = tk.StringVar()
        self.release_notes_var.set(self.server.config.release_notes)
        tk.Entry(self, width=80, textvariable=self.release_notes_var).grid(sticky=tk.W)

    def set_clone_item_frame(self, items_list: list):
        if not self.set_combobox_items_frame(items_list=items_list):
            return

        tk.Label(self, text="New item name to be cloned (grayed out if the item has no name): ").grid(sticky=tk.W)
        self.new_name_entry = tk.Entry(self, width=40, textvariable=self.new_item_name_var)
        self.new_name_entry.grid(sticky=tk.W)
        self.set_new_item_name()

        self.set_overwrite_widget()

    def set_new_item_name(self, event=None):
        logger.info(msg=str(event))
        if SubmitWidgets.DIVIDER_BAR in self.item_id_name_var.get():
            item_name_id = self.item_id_name_var.get().split(SubmitWidgets.DIVIDER_BAR)
            item_name = item_name_id[0]
            self.new_item_name_var.set(item_name)
            item_id = item_name_id[1]
        else:
            self.new_name_entry.config(state=tk.DISABLED)
            item_id = self.item_id_name_var.get()
        self.source.config.item_id = item_id
        self.source.config.item_name = ""

    @staticmethod
    def construct_item_name_id_text(item: dict):
        if not item:
            return None
        elif item.get(name_key) and item.get(id_key):
            return item.get(name_key) + SubmitWidgets.DIVIDER_BAR + item.get(id_key)
        elif item.get(id_key):
            return item.get(id_key)
        else:
            return ""

    def set_combobox_items_frame(self, items_list: list):
        if not items_list:
            messagebox.showerror(title=f"No item", message=f"{self.server.config.type} has no item")
            self.submit_button.config(state=tk.DISABLED)
            return False

        self.new_item_name_var = tk.StringVar()

        default_item = find_item(lst=items_list, key=id_key, value=self.source.config.item_id)
        default_text = SubmitWidgets.construct_item_name_id_text(item=default_item)
        texts_list = [SubmitWidgets.construct_item_name_id_text(item=item) for item in items_list]
        self.item_id_name_var = CommonWidgets.set_combobox_items_frame(
            parent=self, texts_list=texts_list, bind_func=self.set_new_item_name, default_text=default_text,
            title=f"Select an item for type {self.server.config.type} (item name|id, or id only for items without "
                  f"name):")

        return True

    def set_radio_channels_frame(self):
        channels_list = self.server.get_list_items_by_conditional_id(
            item_type=item_type_channels, condition_key=project_id_key, condition_id=self.server.config.project_id)
        self.channel_id_var = CommonWidgets.set_radio_items_frame(
            parent=self, list_items=channels_list, default_id=self.server.config.channel_id,
            title=f"Select a channel:")

    def set_clone_space_frame(self):
        tk.Label(self, text=f"Options", bd=2).grid(sticky=tk.W)
        self.set_overwrite_widget()

    def set_overwrite_widget(self):
        self.overwrite_var = tk.StringVar()
        tk.Checkbutton(self, text="Overwrite the existing entities with the same name (skip if unchecked)",
                       variable=self.overwrite_var).grid(sticky=tk.W)
        self.overwrite_var.set(CommonWidgets.SELECTED if self.server.config.overwrite else CommonWidgets.UNSELECTED)

    def process_config(self):
        if self.overwrite_var:
            self.server.config.overwrite = True if self.overwrite_var.get() == CommonWidgets.SELECTED else False
        if self.server.config.action == Actions.ACTION_CREATE_RELEASE:
            self.server.config.channel_id = self.channel_id_var.get()
            self.server.config.release_version = self.release_version_var.get()
            self.server.config.release_notes = self.release_notes_var.get()
        self.server.config.save_config()
        self.source.config.save_config()
        return True

    def run_thread(self):
        if self.server.config.action == Actions.ACTION_CLONE_SPACE:
            msg = f"Are you sure you want to clone types {self.server.config.types} from " \
                  f"{self.source.config.space_id} on server {self.source.config.endpoint} to " \
                  f"{self.server.config.space_id} on server {self.server.config.endpoint}? " \
                  f"The existing entities with the same name will " \
                  f"{' ' if self.server.config.overwrite else 'NOT '}be overwritten."
            if messagebox.askyesno(title=f"{self.server.config.action}", message=msg):
                Migration(src_config=self.source.config, dst_config=self.server.config).clone_space_types()
        elif self.server.config.action == Actions.ACTION_CLONE_SPACE_ITEM:
            # msg = f"cloning {item_type} {item_badge} from {self._src_config.space_id} on server "
            # f"{self._src_config.endpoint} to {self._dst_config.space_id} on server {self._dst_config.endpoint}")
            msg = f"Are you sure you want to clone type {self.server.config.type} of {self.item_id_name_var.get()}" \
                  f" from {self.source.config.space_id} on server {self.source.config.endpoint} to " \
                  f"{self.new_item_name_var.get()} in {self.server.config.space_id} on server " \
                  f"{self.server.config.endpoint}? The existing entities with the same name will " \
                  f"{' ' if self.server.config.overwrite else 'NOT '}be overwritten."
            if messagebox.askyesno(title=f"{self.server.config.action}", message=msg):
                pars_dict = None
                if self.new_item_name_var.get():
                    pars_dict = {Constants.NEW_ITEM_NAME_KEY: self.new_item_name_var.get()}
                Migration(src_config=self.source.config, dst_config=self.server.config) \
                    .clone_space_item_new_name(pars_dict=pars_dict)
        elif self.server.config.action == Actions.ACTION_CLONE_PROJECT_RELATED:
            msg = f"Are you sure you want to clone type {self.server.config.type} of {self.item_id_name_var.get()}" \
                  f" from {self.source.config.space_id} on server {self.source.config.endpoint} to " \
                  f"{self.new_item_name_var.get()} in projects {self.server.config.project_ids} in " \
                  f"{self.server.config.space_id} on server {self.server.config.endpoint}? " \
                  f"The existing entities with the same name will " \
                  f"{' ' if self.server.config.overwrite else 'NOT '}be overwritten."
            if messagebox.askyesno(title=f"{self.server.config.action}", message=msg):
                pars_dict = {Constants.NEW_ITEM_NAME_KEY: self.new_item_name_var.get(),
                             Constants.PROJECT_IDS_KEY: self.server.config.project_ids}
                Migration(src_config=self.source.config, dst_config=self.server.config) \
                    .clone_space_item_new_name(pars_dict=pars_dict)
        elif self.server.config.action == Actions.ACTION_CREATE_RELEASE:
            project_name = self.server.get_or_delete_single_item_by_id(
                item_type=item_type_projects, item_id=self.server.config.project_id).get(name_key)
            channel_name = self.server.get_or_delete_single_item_by_id(
                item_type=item_type_channels, item_id=self.server.config.channel_id).get(name_key)
            msg = f"Are you sure you want to create a new release for project {project_name} with release version " \
                  f"{self.server.config.release_version}, and channel {channel_name}, release notes " \
                  f"{self.server.config.release_notes}?"
            if messagebox.askyesno(title=f"{self.server.config.action}", message=msg):
                ReleaseDeployment.create_release_direct(
                    config=self.server.config, release_version=self.server.config.release_version,
                    project_name=project_name, channel_name=channel_name, notes=self.server.config.release_notes)
        else:
            print("not a valid action")

    def start_run(self):
        threading.Thread(target=self.run_thread).start()

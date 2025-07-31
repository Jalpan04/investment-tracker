import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import simpledialog
import json
import uuid


# --- Application ---
# A complete, standalone application for managing family wealth data.
# This version is person-centric and supports joint ownership of assets.
# It has NO EXTERNAL DEPENDENCIES and should run with a standard Python installation.

class WealthApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Family Wealth Management")
        self.geometry("1300x800")

        self.current_file_path = None

        # --- Style Configuration ---
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TNotebook.Tab", padding=[12, 6], font=('Helvetica', 10, 'bold'))
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'), background="#d0d0d0", relief="flat")
        style.configure("Treeview", rowheight=28, font=('Helvetica', 10), fieldbackground="#f0f0f0")
        style.map("Treeview.Heading", relief=[('active', 'groove'), ('pressed', 'sunken')])
        style.configure("TButton", padding=6, font=('Helvetica', 10))
        style.configure("Bold.TLabel", font=('Helvetica', 11, 'bold'))

        self.data_store = self.initialize_data_structures()
        self.treeviews = {}

        # --- Main UI Structure ---
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.load_data_from_file)
        file_menu.add_command(label="Save", command=self.save_data_to_file)
        file_menu.add_command(label="Save As...", command=self.save_data_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.populate_tabs()
        self.update_title()

    def initialize_data_structures(self):
        """
        Initializes the data structure to hold columns and data for each section,
        matching the desired JSON format.
        """
        return {
            'family_info': {
                'columns': ['Name', 'Aadhar No.', 'PAN no', 'Voter id no'],
                'data': []
            },
            'bank_accounts': {
                'columns': ['Holders', 'Account Type', 'BANK NAME', 'ACCOUNT NO'],
                'data': []
            },
            'fixed_deposits': {
                'columns': ['Holders', 'Bank Name', 'Rate (%)', 'Number of Days', 'Start Date', 'End Date', 'Amount'],
                'data': []
            },
            'demat_accounts': {
                'columns': ['Holders', 'Provider', 'Account Number'],
                'data': []
            },
            'mutual_funds': {
                'columns': ['Holders', 'Provider', 'Fund Name', 'Folio Number'],
                'data': []
            },
            'investments': {
                'columns': ['Holders', 'BANK NAME', 'ACCOUNT NO', 'Details'],
                'data': []
            },
            'insurance': {
                'columns': ['Holders', 'COMPANY', 'POLICY NO', 'SUM ASSURED'],
                'data': []
            },
            'locker': {
                'columns': ['Holders', 'BANK NAME', 'LOCKER NO'],
                'data': []
            },
            'vehicle_details': {
                'columns': ['Owners', 'VEHICLE MAKE', 'REGISTRATION NO'],
                'data': []
            },
            'property': {
                'columns': ['Owners', 'PROPERTY DETAILS', 'LOCATION'],
                'data': []
            }
        }

    def populate_tabs(self):
        """Creates the main tabs for Members and Asset Categories."""
        # The first tab is always for family_info
        self.create_members_tab()

        # Define the order of asset tabs
        asset_sections = [
            'bank_accounts',
            'fixed_deposits',
            'demat_accounts',
            'mutual_funds',
            'investments',
            'insurance',
            'locker',
            'vehicle_details',
            'property'
        ]

        # Create tabs for all other asset sections
        for section_title in asset_sections:
            if section_title in self.data_store:
                self.create_asset_tab(section_title)

    def create_members_tab(self):
        """Creates the main tab for managing family members and viewing their assets."""
        members_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(members_frame, text="Family Info")

        top_pane = ttk.Frame(members_frame)
        top_pane.pack(fill='both', expand=True, pady=(0, 10))
        top_pane.grid_rowconfigure(0, weight=1)
        top_pane.grid_columnconfigure(0, weight=1)
        top_pane.grid_columnconfigure(1, weight=1)

        member_list_frame = ttk.Labelframe(top_pane, text="All Members", padding=10)
        member_list_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        member_list_frame.grid_rowconfigure(1, weight=1)
        member_list_frame.grid_columnconfigure(0, weight=1)

        member_controls = ttk.Frame(member_list_frame)
        member_controls.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        ttk.Button(member_controls, text="Add Member", command=self.add_edit_member).pack(side='left', padx=(0, 5))
        ttk.Button(member_controls, text="Edit Member", command=lambda: self.add_edit_member(edit=True)).pack(
            side='left', padx=(0, 5))
        ttk.Button(member_controls, text="Delete Member", command=self.delete_member).pack(side='left')

        tree_frame = self.create_treeview(member_list_frame, 'family_info')
        tree_frame.grid(row=1, column=0, sticky='nsew')
        self.treeviews['family_info'].bind('<<TreeviewSelect>>', self.display_member_assets)

        assets_view_frame = ttk.Labelframe(top_pane, text="Assets of Selected Member", padding=10)
        assets_view_frame.grid(row=0, column=1, sticky='nsew')
        assets_view_frame.grid_rowconfigure(0, weight=1)
        assets_view_frame.grid_columnconfigure(0, weight=1)
        self.member_asset_text = tk.Text(assets_view_frame, wrap='word', state='disabled', font=('Helvetica', 10),
                                         relief='flat', background=self.cget('bg'))
        self.member_asset_text.grid(row=0, column=0, sticky='nsew')

    def create_asset_tab(self, section_title):
        """Creates a generic tab for an asset category."""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=section_title.replace('_', ' ').title())

        controls_frame = ttk.Frame(tab_frame)
        controls_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(controls_frame, text="Add New Record", command=lambda s=section_title: self.add_edit_asset(s)).pack(
            side='left', padx=(0, 5))
        ttk.Button(controls_frame, text="Edit Selected",
                   command=lambda s=section_title: self.add_edit_asset(s, edit=True)).pack(side='left', padx=(0, 5))
        ttk.Button(controls_frame, text="Delete Selected", command=lambda s=section_title: self.delete_asset(s)).pack(
            side='left')

        tree_frame = self.create_treeview(tab_frame, section_title)
        tree_frame.pack(expand=True, fill='both')

    def create_treeview(self, parent, section_title):
        """Creates a self-contained frame with a treeview and scrollbars."""
        tree_container = ttk.Frame(parent)
        columns = self.data_store[section_title]['columns']
        tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse")
        self.treeviews[section_title] = tree

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        tree.pack(side='left', fill='both', expand=True)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor='w')

        return tree_container

    def refresh_all_views(self):
        """Refreshes all treeviews in the application."""
        for section in self.data_store.keys():
            if section in self.treeviews:
                self.refresh_treeview(section)
        self.display_member_assets()

    def refresh_treeview(self, section_title):
        """Refreshes a single treeview with data."""
        tree = self.treeviews[section_title]
        for item in tree.get_children():
            tree.delete(item)

        columns = self.data_store[section_title]['columns']
        data_rows = self.data_store[section_title]['data']

        if section_title == 'family_info':
            for record in data_rows:
                values = [record.get(col, '') for col in columns]
                tree.insert("", "end", iid=record.get('id'), values=values)
        else:  # Asset sections
            for record in data_rows:
                holder_ids = record.get('holders', [])
                holder_names = [
                    member.get('Name', 'Unknown')
                    for member in (self.get_member_by_id(hid) for hid in holder_ids)
                    if member
                ]

                values = [', '.join(holder_names)]
                other_cols = [col for col in columns if col not in ['Holders', 'Owners']]
                for col in other_cols:
                    values.append(record.get(col, ''))

                tree.insert("", "end", iid=record.get('id'), values=values)

    def display_member_assets(self, event=None):
        """Displays all assets linked to the selected member."""
        self.member_asset_text.config(state='normal')
        self.member_asset_text.delete('1.0', tk.END)

        selected_items = self.treeviews['family_info'].selection()
        if not selected_items:
            self.member_asset_text.config(state='disabled')
            return

        member_id = selected_items[0]
        member = self.get_member_by_id(member_id)
        if not member:
            self.member_asset_text.config(state='disabled')
            return

        self.member_asset_text.insert(tk.END, f"Assets for: {member.get('Name', '')}\n", 'h1')
        self.member_asset_text.insert(tk.END, "=" * 40 + "\n\n")

        for section_title, content in self.data_store.items():
            if section_title == 'family_info': continue

            member_assets = [asset for asset in content['data'] if member_id in asset.get('holders', [])]
            if member_assets:
                self.member_asset_text.insert(tk.END, f"{section_title.replace('_', ' ').title()}\n", 'h2')
                for asset in member_assets:
                    details = ', '.join(f"{k}: {v}" for k, v in asset.items() if k not in ['id', 'holders'])
                    self.member_asset_text.insert(tk.END, f"  • {details}\n")
                self.member_asset_text.insert(tk.END, "\n")

        self.member_asset_text.tag_config('h1', font=('Helvetica', 12, 'bold', 'underline'))
        self.member_asset_text.tag_config('h2', font=('Helvetica', 10, 'bold'))
        self.member_asset_text.config(state='disabled')

    def get_member_by_id(self, member_id):
        """Safely retrieves a member by their ID."""
        return next((m for m in self.data_store['family_info']['data'] if m.get('id') == member_id), None)

    def add_edit_member(self, edit=False):
        initial_data = None
        member_id = None
        if edit:
            selected = self.treeviews['family_info'].selection()
            if not selected:
                messagebox.showwarning("Selection Error", "Please select a member to edit.")
                return
            member_id = selected[0]
            initial_data = self.get_member_by_id(member_id)

        RecordEditorWindow(self, 'family_info', self.save_member, initial_data, member_id)

    def save_member(self, section_title, new_data, member_id):
        """Saves a new or existing member. Corrected signature."""
        if member_id:
            member = self.get_member_by_id(member_id)
            if member: member.update(new_data)
        else:
            new_data['id'] = str(uuid.uuid4())
            self.data_store['family_info']['data'].append(new_data)
        self.refresh_treeview('family_info')

    def delete_member(self):
        """Deletes a member and removes them from all assets."""
        selected = self.treeviews['family_info'].selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a member to delete.")
            return
        member_id = selected[0]
        member = self.get_member_by_id(member_id)

        if not member:
            messagebox.showerror("Error", "Could not find the selected member to delete.")
            return

        member_name = member.get('Name', 'this member')

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete '{member_name}'?\nThis will also remove them from all joint assets."):
            self.data_store['family_info']['data'] = [m for m in self.data_store['family_info']['data'] if
                                                      m.get('id') != member_id]
            for section_content in self.data_store.values():
                # Check if the section is an asset section with 'holders'
                if 'data' in section_content and 'columns' in section_content and (
                        'Holders' in section_content['columns'] or 'Owners' in section_content['columns']):
                    for asset in section_content['data']:
                        if member_id in asset.get('holders', []):
                            asset['holders'].remove(member_id)
            self.refresh_all_views()

    def add_edit_asset(self, section_title, edit=False):
        initial_data = None
        asset_id = None
        if edit:
            selected = self.treeviews[section_title].selection()
            if not selected:
                messagebox.showwarning("Selection Error",
                                       f"Please select a record from '{section_title.replace('_', ' ').title()}' to edit.")
                return
            asset_id = selected[0]
            initial_data = next((a for a in self.data_store[section_title]['data'] if a.get('id') == asset_id), None)

        RecordEditorWindow(self, section_title, self.save_asset, initial_data, asset_id)

    def save_asset(self, section_title, new_data, asset_id):
        """Saves a new or existing asset."""
        if asset_id:
            asset = next((a for a in self.data_store[section_title]['data'] if a.get('id') == asset_id), None)
            if asset: asset.update(new_data)
        else:
            new_data['id'] = str(uuid.uuid4())
            self.data_store[section_title]['data'].append(new_data)
        self.refresh_treeview(section_title)
        self.display_member_assets()

    def delete_asset(self, section_title):
        """Deletes an asset record."""
        selected = self.treeviews[section_title].selection()
        if not selected:
            messagebox.showwarning("Selection Error",
                                   f"Please select a record from '{section_title.replace('_', ' ').title()}' to delete.")
            return
        asset_id = selected[0]
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this asset record?"):
            self.data_store[section_title]['data'] = [a for a in self.data_store[section_title]['data'] if
                                                      a.get('id') != asset_id]
            self.refresh_treeview(section_title)
            self.display_member_assets()

    def new_file(self):
        if messagebox.askyesno("Confirm New", "Are you sure? Any unsaved changes will be lost."):
            self.data_store = self.initialize_data_structures()
            self.refresh_all_views()
            self.current_file_path = None
            self.update_title()

    def save_data_to_file(self):
        if not self.current_file_path:
            self.save_data_as()
        else:
            self._write_to_file(self.current_file_path)

    def save_data_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Data Files", "*.json")],
                                                 title="Save Wealth Data")
        if file_path:
            self._write_to_file(file_path)
            self.current_file_path = file_path
            self.update_title()

    def _write_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data_store, f, indent=4)
            messagebox.showinfo("Success", f"Data saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data.\nError: {e}")

    def transform_old_data_format(self, old_data):
        """Transforms data from the old list-based format to the new structured format."""
        new_store = self.initialize_data_structures()

        # Determine the old member key ('members' or 'family_info')
        old_member_key = 'members' if 'members' in old_data else 'family_info'

        # Migrate members
        if old_member_key in old_data and isinstance(old_data[old_member_key], list):
            for member_record in old_data[old_member_key]:
                if 'id' not in member_record:
                    member_record['id'] = str(uuid.uuid4())
                # Ensure keys match the new format ('Name' vs 'name')
                if 'name' in member_record and 'Name' not in member_record:
                    member_record['Name'] = member_record.pop('name')
                new_store['family_info']['data'].append(member_record)

        # Migrate other asset sections
        for section_title, content in new_store.items():
            if section_title == 'family_info':
                continue
            if section_title in old_data and isinstance(old_data[section_title], list):
                for asset_record in old_data[section_title]:
                    if 'id' not in asset_record:
                        asset_record['id'] = str(uuid.uuid4())
                    new_store[section_title]['data'].append(asset_record)

        return new_store

    def load_data_from_file(self):
        """Loads data from a JSON file, transforming old formats if necessary."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Data Files", "*.json")], title="Open Wealth Data")
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Check if data is in the new format or needs transformation
            if 'family_info' in loaded_data and 'columns' in loaded_data['family_info']:
                # It's the new format, load directly
                self.data_store = loaded_data
            elif ('members' in loaded_data and isinstance(loaded_data['members'], list)) or \
                    ('family_info' in loaded_data and isinstance(loaded_data['family_info'], list)):
                # It's an old format, transform it
                messagebox.showinfo("Data Migration",
                                    "Older data format detected. The data will be migrated to the new format. Please re-save the file.")
                self.data_store = self.transform_old_data_format(loaded_data)
            else:
                raise ValueError("Unrecognized or invalid data format in JSON file.")

            # Ensure all sections from the latest structure exist
            for section, content in self.initialize_data_structures().items():
                if section not in self.data_store:
                    self.data_store[section] = content

            self.refresh_all_views()
            self.current_file_path = file_path
            self.update_title()
            messagebox.showinfo("Success", "Data loaded successfully.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load or migrate data.\nError: {e}")
            self.data_store = self.initialize_data_structures()

    def update_title(self):
        base_title = "Family Wealth Management"
        if self.current_file_path:
            self.title(f"{base_title} - [{self.current_file_path.split('/')[-1]}]")
        else:
            self.title(f"{base_title} - [Unsaved]")


class RecordEditorWindow(tk.Toplevel):
    def __init__(self, parent, section_title, save_callback, initial_data=None, record_id=None):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()

        self.parent_app = parent
        self.section_title = section_title
        self.save_callback = save_callback
        self.initial_data = initial_data or {}
        self.record_id = record_id

        self.title(f"{'Edit' if record_id else 'Add'} {section_title.replace('_', ' ').title()}")

        self.entries = {}
        self.holder_listbox = None
        self.bank_combobox = None
        self.bank_col_name = None

        form_frame = ttk.Frame(self, padding="15")
        form_frame.pack(expand=True, fill="both")

        columns = self.parent_app.data_store[section_title]['columns']

        for i, col_name in enumerate(columns):
            ttk.Label(form_frame, text=f"{col_name}:").grid(row=i, column=0, sticky='nw', pady=5, padx=5)

            if col_name in ['Holders', 'Owners']:
                self.holder_listbox = tk.Listbox(form_frame, selectmode='multiple', exportselection=False, height=6)
                self.holder_listbox.grid(row=i, column=1, sticky='ew', pady=5, padx=5)

                self.member_map = {
                    member.get('Name', ''): member.get('id', '')
                    for member in self.parent_app.data_store['family_info']['data']
                }
                for name in self.member_map.keys():
                    self.holder_listbox.insert(tk.END, name)

                current_holder_ids = self.initial_data.get('holders', [])
                for idx, name in enumerate(self.holder_listbox.get(0, tk.END)):
                    if self.member_map.get(name) in current_holder_ids:
                        self.holder_listbox.selection_set(idx)

            elif (self.section_title == 'fixed_deposits' and col_name == 'Bank Name') or \
                    (self.section_title == 'investments' and col_name == 'BANK NAME'):

                self.bank_col_name = col_name  # Store the column name for saving
                bank_names = sorted(list(set(
                    acc.get('BANK NAME', '') for acc in self.parent_app.data_store['bank_accounts']['data'] if
                    acc.get('BANK NAME')
                )))

                self.bank_combobox = ttk.Combobox(form_frame, values=bank_names + ["Add New Bank..."])
                self.bank_combobox.grid(row=i, column=1, sticky='ew', pady=5, padx=5)
                self.bank_combobox.set(self.initial_data.get(col_name, ''))
                self.bank_combobox.bind("<<ComboboxSelected>>", self.check_new_bank)

            else:
                entry = ttk.Entry(form_frame, width=50)
                entry.grid(row=i, column=1, sticky='ew', pady=5, padx=5)
                entry.insert(0, self.initial_data.get(col_name, ''))
                self.entries[col_name] = entry

        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill='x')
        ttk.Button(button_frame, text="Save", command=self.save).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side='right')

    def check_new_bank(self, event):
        """Handle the 'Add New Bank...' selection."""
        if self.bank_combobox.get() == "Add New Bank...":
            new_bank = simpledialog.askstring("New Bank", "Enter the name of the new bank:", parent=self)
            if new_bank:
                # Add to combobox list and select it
                current_values = list(self.bank_combobox['values'])
                if new_bank not in current_values:
                    current_values.insert(-1, new_bank)
                self.bank_combobox['values'] = current_values
                self.bank_combobox.set(new_bank)
            else:
                self.bank_combobox.set('')  # Clear selection if cancelled

    def save(self):
        """Saves the record with correct keys."""
        new_data = {key: entry.get() for key, entry in self.entries.items()}

        if self.holder_listbox:
            selected_indices = self.holder_listbox.curselection()
            selected_names = [self.holder_listbox.get(i) for i in selected_indices]
            new_data['holders'] = [self.member_map[name] for name in selected_names]

        if self.bank_combobox:
            new_data[self.bank_col_name] = self.bank_combobox.get()

        self.save_callback(self.section_title, new_data, self.record_id)
        self.destroy()


if __name__ == "__main__":
    app = WealthApp()
    app.mainloop()

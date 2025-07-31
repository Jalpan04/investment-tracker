import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import uuid
import os
import csv
from datetime import datetime
import sys


# --- Helper function for PyInstaller to find data files ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- Helper Class for Tooltips ---
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if not self.widget.winfo_exists():
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


# --- Main Application ---
class WealthApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Family Wealth Management")
        self.geometry("1400x850")

        try:
            icon_path = resource_path("logo.ico")
            self.iconbitmap(icon_path)
        except tk.TclError:
            print("Warning: Icon file 'logo.ico' not found or invalid. Using default icon.")

        self.current_file_path = None
        self.search_vars = {}

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.configure_style()

        self.data_store = self.initialize_data_structures()
        self.treeviews = {}

        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.load_data_from_file)
        file_menu.add_command(label="Save", command=self.save_data_to_file)
        file_menu.add_command(label="Save As...", command=self.save_data_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export as CSV Files...", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.populate_tabs()
        self.update_title()

    def configure_style(self):
        self.style.configure("TNotebook.Tab", padding=[12, 6], font=('Helvetica', 10, 'bold'))
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'), background="#d0d0d0", relief="flat")
        self.style.configure("Treeview", rowheight=28, font=('Helvetica', 10), fieldbackground="#ffffff")
        self.style.map("Treeview.Heading", relief=[('active', 'groove'), ('pressed', 'sunken')])
        self.style.configure("TButton", padding=6, font=('Helvetica', 10))
        self.style.configure("Bold.TLabel", font=('Helvetica', 11, 'bold'))

    def initialize_data_structures(self):
        base_structures = {
            'family_info': {'columns': ['Name', 'Aadhar No.', 'PAN no', 'Voter id no'], 'data': []},
            'bank_accounts': {'columns': ['Holders', 'Account Type', 'BANK NAME', 'ACCOUNT NO'], 'data': []},
            'fixed_deposits': {
                'columns': ['Holders', 'Bank Name', 'Rate (%)', 'Number of Days', 'Start Date', 'End Date', 'Amount'],
                'data': []},
            'demat_accounts': {'columns': ['Holders', 'Provider', 'Account Number'], 'data': []},
            'mutual_funds': {'columns': ['Holders', 'Provider', 'Fund Name', 'Folio Number'], 'data': []},
            'investments': {'columns': ['Holders', 'BANK NAME', 'ACCOUNT NO', 'Details'], 'data': []},
            'insurance': {'columns': ['Holders', 'COMPANY', 'POLICY NO', 'SUM ASSURED'], 'data': []},
            'locker': {'columns': ['Holders', 'BANK NAME', 'LOCKER NO'], 'data': []},
            'vehicle_details': {'columns': ['Owners', 'VEHICLE MAKE', 'REGISTRATION NO'], 'data': []},
            'property': {'columns': ['Owners', 'PROPERTY DETAILS', 'LOCATION'], 'data': []}
        }
        return base_structures

    def populate_tabs(self):
        self.create_members_tab()
        asset_sections = [
            'bank_accounts', 'fixed_deposits', 'demat_accounts', 'mutual_funds',
            'investments', 'insurance', 'locker', 'vehicle_details', 'property'
        ]
        for section_title in asset_sections:
            if section_title in self.data_store:
                self.create_asset_tab(section_title)

    def create_members_tab(self):
        members_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(members_frame, text="Family Info")

        paned_window = ttk.PanedWindow(members_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill='both', expand=True, pady=(0, 10))

        member_list_frame = ttk.Labelframe(paned_window, text="All Members", padding=10)
        paned_window.add(member_list_frame, weight=1)

        # --- Member-specific controls ---
        member_controls = ttk.Frame(member_list_frame)
        member_controls.pack(fill='x', pady=(0, 10))

        button_add = ttk.Button(member_controls, text="Add Member", command=self.add_member)
        button_add.pack(side='left', padx=(0, 5))
        Tooltip(button_add, "Add a new family member")

        button_edit = ttk.Button(member_controls, text="Edit Member", command=self.edit_member)
        button_edit.pack(side='left', padx=(0, 5))
        Tooltip(button_edit, "Edit the selected member")

        button_delete = ttk.Button(member_controls, text="Delete Member", command=self.delete_member_from_button)
        button_delete.pack(side='left', padx=(0, 15))
        Tooltip(button_delete, "Delete the selected member")

        ttk.Label(member_controls, text="Search:").pack(side='left')
        self.search_vars['family_info'] = tk.StringVar()
        search_entry = ttk.Entry(member_controls, textvariable=self.search_vars['family_info'])
        search_entry.pack(side='left', fill='x', expand=True)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_treeview('family_info'))
        Tooltip(search_entry, "Type to search members in real-time")

        tree_frame = self.create_treeview(member_list_frame, 'family_info')
        tree_frame.pack(expand=True, fill='both')
        self.treeviews['family_info'].bind('<<TreeviewSelect>>', self.display_member_assets)

        assets_view_frame = ttk.Labelframe(paned_window, text="Assets of Selected Member", padding=10)
        paned_window.add(assets_view_frame, weight=2)

        self.member_asset_text = tk.Text(assets_view_frame, wrap='word', state='disabled', font=('Helvetica', 10),
                                         relief='flat', padx=10, pady=10)
        self.member_asset_text.pack(expand=True, fill='both')

        self.member_asset_text.tag_config('h1', font=('Helvetica', 14, 'bold', 'underline'), spacing3=10)
        self.member_asset_text.tag_config('h2', font=('Helvetica', 12, 'bold'), spacing1=10, spacing3=5)
        self.member_asset_text.tag_config('h3', font=('Helvetica', 10, 'italic'), foreground="gray", spacing1=5)
        self.member_asset_text.tag_config('key', font=('Helvetica', 10, 'bold'))
        self.member_asset_text.config(tabs=("150p",))

    def create_asset_tab(self, section_title):
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=section_title.replace('_', ' ').title())
        self.create_asset_controls(tab_frame, section_title)
        tree_frame = self.create_treeview(tab_frame, section_title)
        tree_frame.pack(expand=True, fill='both')

    def create_asset_controls(self, parent, section_title):
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill='x', pady=(0, 10))
        button_add = ttk.Button(controls_frame, text="Add Record", command=lambda s=section_title: self.add_asset(s))
        button_add.pack(side='left', padx=(0, 5))
        Tooltip(button_add, f"Add a new record to {section_title.replace('_', ' ').title()}")
        button_edit = ttk.Button(controls_frame, text="Edit Record", command=lambda s=section_title: self.edit_asset(s))
        button_edit.pack(side='left', padx=(0, 5))
        Tooltip(button_edit, "Edit the selected record")
        button_delete = ttk.Button(controls_frame, text="Delete Record",
                                   command=lambda s=section_title: self.delete_asset(s))
        button_delete.pack(side='left', padx=(0, 15))
        Tooltip(button_delete, "Delete the selected record")
        ttk.Label(controls_frame, text="Search:").pack(side='left')
        self.search_vars[section_title] = tk.StringVar()
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_vars[section_title])
        search_entry.pack(side='left', fill='x', expand=True)
        search_entry.bind('<KeyRelease>', lambda e, s=section_title: self.filter_treeview(s))
        Tooltip(search_entry, "Type to search records in real-time")

    def create_treeview(self, parent, section_title):
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
            tree.heading(col, text=col, anchor='w')
            tree.column(col, width=140, anchor='w')
        tree.bind("<Button-3>", lambda e, s=section_title: self.show_context_menu(e, s))
        return tree_container

    def show_context_menu(self, event, section_title):
        tree = self.treeviews[section_title]
        item_id = tree.identify_row(event.y)
        if not item_id: return
        tree.selection_set(item_id)
        context_menu = tk.Menu(self, tearoff=0)

        if section_title == 'family_info':
            context_menu.add_command(label="Edit Member", command=self.edit_member)
            context_menu.add_command(label="Delete Member", command=self.delete_member_from_button)
        else:
            context_menu.add_command(label="Edit Record", command=lambda s=section_title: self.edit_asset(s))
            context_menu.add_command(label="Delete Record", command=lambda s=section_title: self.delete_asset(s))
        context_menu.post(event.x_root, event.y_root)

    def filter_treeview(self, section_title):
        search_term = self.search_vars[section_title].get().lower()
        all_records = self.data_store[section_title]['data']
        if not search_term:
            self.refresh_treeview(section_title, all_records)
            return
        filtered_records = [rec for rec in all_records if any(search_term in str(val).lower() for val in rec.values())]
        self.refresh_treeview(section_title, filtered_records)

    def refresh_all_views(self):
        for section in self.data_store.keys():
            if section in self.treeviews:
                self.filter_treeview(section)
        self.display_member_assets()

    def refresh_treeview(self, section_title, data_to_display=None):
        tree = self.treeviews[section_title]
        for item in tree.get_children(): tree.delete(item)
        data_rows = data_to_display if data_to_display is not None else self.data_store[section_title]['data']
        columns = self.data_store[section_title]['columns']
        for record in data_rows:
            values = []
            for col in columns:
                if col in ['Holders', 'Owners']:
                    holder_ids = record.get('holders', [])
                    holder_names = [m.get('Name', '?') for m in (self.get_member_by_id(hid) for hid in holder_ids) if m]
                    values.append(', '.join(holder_names))
                else:
                    values.append(record.get(col, ''))
            tree.insert("", "end", iid=record.get('id'), values=values)

    def display_member_assets(self, event=None):
        self.member_asset_text.config(state='normal')
        self.member_asset_text.delete('1.0', tk.END)
        selected = self.treeviews['family_info'].selection()
        if not selected:
            self.member_asset_text.config(state='disabled')
            return
        member = self.get_member_by_id(selected[0])
        if not member:
            self.member_asset_text.config(state='disabled')
            return
        self.member_asset_text.insert(tk.END, f"Assets for: {member.get('Name', '')}\n", 'h1')
        for section, content in self.data_store.items():
            if section == 'family_info': continue
            member_assets = [asset for asset in content['data'] if member.get('id') in asset.get('holders', [])]
            if member_assets:
                self.member_asset_text.insert(tk.END, f"{section.replace('_', ' ').title()}\n", 'h2')
                for asset in member_assets:
                    title = asset.get('Fund Name') or asset.get('PROPERTY DETAILS') or asset.get(
                        'POLICY NO') or f"ID: {asset.get('id')[:8]}"
                    self.member_asset_text.insert(tk.END, f"  • {title}\n", 'h3')
                    for k, v in asset.items():
                        if k in ['id', 'holders'] or not v: continue
                        key_display = k.replace('_', ' ').title()
                        self.member_asset_text.insert(tk.END, f"\t{key_display}:\t", 'key')
                        self.member_asset_text.insert(tk.END, f"{v}\n")
                self.member_asset_text.insert(tk.END, "\n")
        self.member_asset_text.config(state='disabled')

    def get_member_by_id(self, member_id):
        return next((m for m in self.data_store['family_info']['data'] if m.get('id') == member_id), None)

    # --- Member specific actions ---
    def add_member(self):
        RecordEditorWindow(self, 'family_info', self.save_member, initial_data=None, record_id=None)

    def edit_member(self):
        selected = self.treeviews['family_info'].selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a member to edit.")
            return
        record_id = selected[0]
        initial_data = self.get_member_by_id(record_id)
        RecordEditorWindow(self, 'family_info', self.save_member, initial_data, record_id)

    def save_member(self, _, new_data, member_id):
        if member_id:
            member = self.get_member_by_id(member_id)
            if member: member.update(new_data)
        else:
            new_data['id'] = str(uuid.uuid4())
            self.data_store['family_info']['data'].append(new_data)
        self.filter_treeview('family_info')

    def delete_member_from_button(self):
        selected = self.treeviews['family_info'].selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a member to delete.")
            return
        member = self.get_member_by_id(selected[0])
        if not member: return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete '{member.get('Name')}'?\nThis will remove them from all assets."):
            self.data_store['family_info']['data'] = [m for m in self.data_store['family_info']['data'] if
                                                      m.get('id') != member.get('id')]
            for section in self.data_store.values():
                if isinstance(section, dict) and 'data' in section:
                    for asset in section['data']:
                        if 'holders' in asset and member.get('id') in asset['holders']:
                            asset['holders'].remove(member.get('id'))
            self.refresh_all_views()

    # --- Asset specific actions ---
    def add_asset(self, section_title):
        RecordEditorWindow(self, section_title, self.save_asset, initial_data=None, record_id=None)

    def edit_asset(self, section_title):
        selected = self.treeviews[section_title].selection()
        if not selected:
            messagebox.showwarning("Selection Error",
                                   f"Please select a record from '{section_title.replace('_', ' ').title()}' to edit.")
            return
        record_id = selected[0]
        initial_data = next((a for a in self.data_store[section_title]['data'] if a.get('id') == record_id), None)
        RecordEditorWindow(self, section_title, self.save_asset, initial_data, record_id)

    def save_asset(self, section_title, new_data, asset_id):
        if asset_id:
            asset = next((a for a in self.data_store[section_title]['data'] if a.get('id') == asset_id), None)
            if asset: asset.update(new_data)
        else:
            new_data['id'] = str(uuid.uuid4())
            self.data_store[section_title]['data'].append(new_data)
        self.filter_treeview(section_title)
        self.display_member_assets()

    def delete_asset(self, section_title):
        selected = self.treeviews[section_title].selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a record to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this asset record?"):
            self.data_store[section_title]['data'] = [a for a in self.data_store[section_title]['data'] if
                                                      a.get('id') != selected[0]]
            self.filter_treeview(section_title)
            self.display_member_assets()

    # --- File and Export Operations ---
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

    def load_data_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Data Files", "*.json")], title="Open Wealth Data")
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            if 'family_info' not in loaded_data or 'columns' not in loaded_data['family_info']:
                raise ValueError("Unrecognized data format.")
            self.data_store = self.initialize_data_structures()
            self.data_store.update(loaded_data)
            self.refresh_all_views()
            self.current_file_path = file_path
            self.update_title()
            messagebox.showinfo("Success", "Data loaded successfully.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load or migrate data.\nError: {e}")
            self.new_file()

    def export_to_csv(self):
        if not any(content['data'] for content in self.data_store.values()):
            messagebox.showwarning("Export Empty", "There is no data to export.")
            return
        directory = filedialog.askdirectory(title="Select a Folder to Save CSV Files")
        if not directory:
            return
        try:
            for section_title, content in self.data_store.items():
                if not content['data']: continue
                records_to_write = []
                original_records = [dict(r) for r in content['data']]
                for record in original_records:
                    if 'holders' in record:
                        holder_ids = record.pop('holders', [])
                        holder_names = [
                            (self.get_member_by_id(hid).get('Name', '?') if self.get_member_by_id(hid) else '?') for hid
                            in holder_ids]
                        record['Owners' if 'Owners' in content['columns'] else 'Holders'] = ', '.join(holder_names)
                    record.pop('id', None)
                    records_to_write.append(record)
                if not records_to_write: continue
                fieldnames = list(records_to_write[0].keys())
                file_path = os.path.join(directory, f"{section_title}.csv")
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records_to_write)
            messagebox.showinfo("Export Successful", f"Data exported to:\n{directory}")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export:\n{e}")

    def update_title(self):
        base_title = "Family Wealth Management"
        file_name = os.path.basename(self.current_file_path) if self.current_file_path else "Unsaved File"
        self.title(f"{base_title} - [{file_name}]")


# --- Editor Window ---
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
        self.style = ttk.Style(self)
        self.style.theme_use(parent.style.theme_use())
        self.title(f"{'Edit' if record_id else 'Add'} {section_title.replace('_', ' ').title()}")
        self.geometry("600x600")  # Reduced height as attachments are gone
        self.entries = {}
        self.holder_listbox = None
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill="both")
        columns = self.parent_app.data_store[section_title]['columns']
        row_counter = 0
        for col_name in columns:
            ttk.Label(main_frame, text=f"{col_name}:").grid(row=row_counter, column=0, sticky='nw', pady=5, padx=5)
            if col_name in ['Holders', 'Owners']:
                self.holder_listbox = tk.Listbox(main_frame, selectmode='multiple', exportselection=False, height=5)
                self.holder_listbox.grid(row=row_counter, column=1, sticky='ew', pady=5, padx=5)
                self.member_map = {m.get('Name', ''): m.get('id', '') for m in
                                   self.parent_app.data_store['family_info']['data']}
                for name in self.member_map.keys():
                    self.holder_listbox.insert(tk.END, name)
                current_holder_ids = self.initial_data.get('holders', [])
                for idx, name in enumerate(self.holder_listbox.get(0, tk.END)):
                    if self.member_map.get(name) in current_holder_ids:
                        self.holder_listbox.selection_set(idx)
            else:
                entry = ttk.Entry(main_frame, width=50)
                entry.grid(row=row_counter, column=1, sticky='ew', pady=5, padx=5)
                entry.insert(0, self.initial_data.get(col_name, ''))
                self.entries[col_name] = entry
            row_counter += 1

        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill='x', side='bottom')
        ttk.Button(button_frame, text="Save", command=self.save).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side='right')

    def validate(self):
        for key, entry in self.entries.items():
            value = entry.get()
            if not value: continue
            if any(k in key.lower() for k in ['amount', 'rate', 'sum assured', 'days']):
                try:
                    float(value)
                except ValueError:
                    messagebox.showerror("Validation Error",
                                         f"Invalid input for '{key}'.\nPlease enter a valid number.", parent=self)
                    return False
            if 'date' in key.lower():
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    messagebox.showwarning("Validation Warning",
                                           f"Invalid format for '{key}'.\nRecommended format is YYYY-MM-DD.",
                                           parent=self)
        return True

    def save(self):
        if not self.validate(): return
        new_data = {key: entry.get() for key, entry in self.entries.items()}
        if self.holder_listbox:
            selected_indices = self.holder_listbox.curselection()
            selected_names = [self.holder_listbox.get(i) for i in selected_indices]
            new_data['holders'] = [self.member_map[name] for name in selected_names]

        self.save_callback(self.section_title, new_data, self.record_id)
        self.destroy()


if __name__ == "__main__":
    app = WealthApp()
    app.mainloop()
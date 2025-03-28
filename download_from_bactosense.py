"""
Downloads files from bactosense device
Adrian Shajkofci - 08/2023
bNovate Technologies SA
"""

import os
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class BactosenseDownloader:
    def __init__(self, root):
        self.root = root
        root.title("Bactosense Data Downloader v2")
        root.geometry("600x500")
        
        # Add abort flag
        self.abort_download = False
        
        # Create a frame for inputs
        input_frame = ttk.Frame(root, padding="10")
        input_frame.pack(fill=tk.X)

        # IP Address
        ttk.Label(input_frame, text="IP Address or URL:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.ip_address = ttk.Entry(input_frame, width=30)
        self.ip_address.grid(column=1, row=0, sticky=tk.W, padx=5)

        # Username
        ttk.Label(input_frame, text="User name (admin, service):").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.username = ttk.Entry(input_frame, width=30)
        self.username.grid(column=1, row=1, sticky=tk.W, padx=5)
        self.username.insert(0, "admin")

        # Password
        ttk.Label(input_frame, text="Password:").grid(column=0, row=2, sticky=tk.W, pady=5)
        self.password = ttk.Entry(input_frame, width=30, show="*")
        self.password.grid(column=1, row=2, sticky=tk.W, padx=5)

        # Download options
        ttk.Label(input_frame, text="Download all files or only FCS?").grid(column=0, row=3, sticky=tk.W, pady=5)
        self.download_option = tk.StringVar(value="n")
        download_frame = ttk.Frame(input_frame)
        download_frame.grid(column=1, row=3, sticky=tk.W, padx=5)
        ttk.Radiobutton(download_frame, text="All files", variable=self.download_option, value="y").pack(side=tk.LEFT)
        ttk.Radiobutton(download_frame, text="Only FCS", variable=self.download_option, value="n").pack(side=tk.LEFT)

        # Replace the download button section with a button frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(column=0, row=4, columnspan=2, pady=10)
        
        # Download button
        self.download_button = ttk.Button(button_frame, text="Start Download", command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        # Abort button
        self.abort_button = ttk.Button(button_frame, text="Abort", command=self.abort_download_process, state=tk.DISABLED)
        self.abort_button.pack(side=tk.LEFT, padx=5)

        # Output console
        ttk.Label(root, text="Console Output:").pack(anchor=tk.W, padx=10)
        self.console = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20)
        self.console.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.console.configure(state="disabled")

        # Redirect stdout to our console
        self.redirect = RedirectText(self.console)
        sys.stdout = self.redirect

        print("Bactosense data downloader v2")

    def start_download(self):
        # Reset abort flag
        self.abort_download = False
        
        # Enable abort button, disable download button
        self.abort_button.config(state=tk.NORMAL)
        self.download_button.config(state=tk.DISABLED)
        
        # Get input values
        ip = self.ip_address.get().strip()
        ip = ip.replace("http://", "").replace("https://", "")
        login = self.username.get().strip().lower()
        password = self.password.get().strip()
        download_all = self.download_option.get()
        
        # Start download in a separate thread to keep UI responsive
        download_thread = threading.Thread(
            target=self.download_process,
            args=(ip, login, password, download_all)
        )
        download_thread.daemon = True
        download_thread.start()
    
    def abort_download_process(self):
        # Set the abort flag
        self.abort_download = True
        print("Aborting download... Please wait.")
        
        # Disable the abort button to prevent multiple clicks
        self.abort_button.config(state=tk.DISABLED)

    def download_process(self, ip_address, login, password, download_all):
        print("Working...")
        
        def download_csv(diagnostics_url, date_string, name, subdir, extension=".csv"):
            diagnostics_url = diagnostics_url[:-1]
            diagnostics_url.append("debug")
            diagnostics_url.append(date_string + "_" + name + extension)
            diagnostics_url = "/".join(diagnostics_url)
            downloaded_diagnostics = requests.get(
                "http://"+ip_address+diagnostics_url, auth=(login, password))
            
            if downloaded_diagnostics.status_code != 200:
                print("ERROR: Cannot download {} {}".format(name, diagnostics_url))
                return
            try:
                with open(subdir + date_string + "_" + name + extension, "wb") as f:
                    f.write(downloaded_diagnostics.content)
            except Exception as e:
                print(str(e))

        try:
            data = requests.get("http://"+ip_address+"/data",
                            auth=(login, password)).json()
            subdir = ""
            ip_address_dir = ip_address.replace(".", "_")
            try:
                os.makedirs(ip_address_dir)
            except:
                pass
            for bucket, bucket_content in data.items():
                # Check for abort
                if self.abort_download:
                    print("Download aborted by user.")
                    break
                
                if bucket in ["auto", "manual"]:
                    try:
                        os.makedirs(ip_address_dir+ "/"+bucket)
                    except:
                        pass
                    subdir = ip_address_dir+ "/" +bucket + "/"
                    for item in bucket_content:
                        # Check for abort
                        if self.abort_download:
                            print("Download aborted by user.")
                            break
                            
                        fcs_file = item['fcsPath'].replace("/archive", "")
                        archive_path = item['archivePath'].replace("/archive", "")
                        try:
                            diagnostics_url = item['fcsUrl'].split("/")
                            only_date_string = diagnostics_url[-1].split("_")[0]
                            date_string = only_date_string +" "+ item['name']
                            subdir = ip_address_dir + "/" + bucket + "/" + date_string + "/"
                            try:
                                os.makedirs(subdir)
                            except:
                                pass
                            print("Downloading " + date_string + "...")
                            downloaded_fcs = requests.get(
                                "http://"+ip_address+item['fcsUrl'], auth=(login, password))
                            if len(downloaded_fcs.content) < 200:
                                print("ERROR: FCS file too small {} {}".format(
                                    item['name'], fcs_file))
                            try:
                                with open(subdir+date_string + "_events.fcs", "wb") as f:
                                    f.write(downloaded_fcs.content)
                            except Exception as e:
                                print(str(e))
                                
                            downloaded_png = requests.get(
                                "http://"+ip_address+item['summaryUrl'], auth=(login, password))
                            try:
                                with open(subdir+date_string + "_summary.png", "wb") as f:
                                    f.write(downloaded_png.content)
                                    
                            except Exception as e:
                                print(str(e))
                                
                            if download_all == "n":
                                continue
                            debug_subdir= subdir + "debug/"
                            try:
                                os.makedirs(debug_subdir)
                            except:
                                pass
                            download_csv(diagnostics_url, only_date_string, "diagnostics", debug_subdir)
                            download_csv(diagnostics_url, only_date_string, "signal_errors", debug_subdir)
                            download_csv(diagnostics_url, only_date_string, "results", debug_subdir, extension=".json")
                            download_csv(diagnostics_url, only_date_string, "gate", debug_subdir, extension=".json")
                            
                        except Exception as e:
                            print("ERROR: FCS file cannot be downloaded {} {}".format(
                                item['name'], fcs_file))
                            print(str(e))
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            # Reset button states
            self.root.after(0, self.reset_buttons)
            if not self.abort_download:
                print("Download completed.")
    
    def reset_buttons(self):
        # Reset buttons to their initial states
        self.download_button.config(state=tk.NORMAL)
        self.abort_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = BactosenseDownloader(root)
    root.mainloop()

"""
Downloads files from bactosense device
Adrian Shajkofci - 08/2023
bNovate Technologies SA
"""

import os
import requests
print("Bactosense data downloader v2")
ip_address = input("IP Address of the Bactosense: ").strip()
login = input("User name (admin, service): ").strip().lower()
password = input("Password: ").strip()
download_all = input("Download all files or only fcs? (y=all files/n): ").strip().lower()
print("Working...")

def download_csv(diagnostics_url, date_string, name, subdir, extension=".csv"):

    diagnostics_url = diagnostics_url[:-1]
    diagnostics_url.append("debug")
    diagnostics_url.append(date_string + "_" + name + extension)
    diagnostics_url = "/".join(diagnostics_url)
    downloaded_diagnostics = requests.get(
        "http://"+ip_address+diagnostics_url, auth=(login, password))
    try:
        with open(subdir + date_string + "_" + name + extension, "wb") as f:
            f.write(downloaded_diagnostics.content)
    except Exception as e:
        print(str(e))

data = requests.get("http://"+ip_address+"/data",
                    auth=(login, password)).json()
subdir = ""
for bucket, bucket_content in data.items():
    if bucket in ["auto", "manual"]:
        try:
            os.makedirs(bucket)
        except:
            pass
        subdir = bucket + "/"
        for item in bucket_content:
            fcs_file = item['fcsPath'].replace("/archive", "")
            archive_path = item['archivePath'].replace("/archive", "")
            try:
                diagnostics_url = item['fcsUrl'].split("/")
                date_string = diagnostics_url[-1].split("_")[0] +" "+ item['name']
                subdir = bucket + "/" + date_string + "/"
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
                download_csv(diagnostics_url, date_string, "diagnostics", debug_subdir)
                download_csv(diagnostics_url, date_string, "counts", debug_subdir)
                download_csv(diagnostics_url, date_string, "offsets", debug_subdir)
                download_csv(diagnostics_url, date_string, "signal_errors", debug_subdir)
                download_csv(diagnostics_url, date_string, "results", debug_subdir, extension=".json")
                download_csv(diagnostics_url, date_string, "gate", debug_subdir, extension=".json")
                
            except:
                print("ERROR: FCS file cannot be downloaded {} {}".format(
                    item['name'], fcs_file))

input("Press ENTER to exit...")

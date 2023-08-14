"""
Downloads files from bactosense device
Adrian Shajkofci - 08/2023
bNovate Technologies SA
"""

import requests

ip_address = input("IP Address of the Bactosense: ").strip()
login = input("User name (admin, service): ").strip().lower()
password = input("Password: ").strip()
print("Working...")

def download_csv(diagnostics_url, date_string, name):

    diagnostics_url = diagnostics_url[:-1]
    diagnostics_url.append("debug")
    diagnostics_url.append(date_string + "_" + name + ".csv")
    diagnostics_url = "/".join(diagnostics_url)
    print("http://"+ip_address+diagnostics_url)
    downloaded_diagnostics = requests.get(
        "http://"+ip_address+diagnostics_url, auth=(login, password))
    try:
        with open(date_string + "_" + name + ".csv", "wb") as f:
            f.write(downloaded_diagnostics.content)
    except Exception as e:
        print(str(e))

data = requests.get("http://"+ip_address+"/data",
                    auth=(login, password)).json()
for bucket, bucket_content in data.items():
    if bucket in ["auto", "manual"]:
        for item in bucket_content:
            fcs_file = item['fcsPath'].replace("/archive", "")
            archive_path = item['archivePath'].replace("/archive", "")
            try:
                diagnostics_url = item['fcsUrl'].split("/")
                date_string = diagnostics_url[-1].split("_")[0]
                
                downloaded_fcs = requests.get(
                    "http://"+ip_address+item['fcsUrl'], auth=(login, password))
                if len(downloaded_fcs.content) < 200:
                    print("ERROR: FCS file too small {} {}".format(
                        item['name'], fcs_file))
                try:
                    with open(date_string + "_events.fcs", "wb") as f:
                        f.write(downloaded_fcs.content)
                except Exception as e:
                    print(str(e))
                    

                
                download_csv(diagnostics_url, date_string, "diagnostics")
                download_csv(diagnostics_url, date_string, "counts")
                download_csv(diagnostics_url, date_string, "offsets")
                download_csv(diagnostics_url, date_string, "signal_errors")
            except:
                print("ERROR: FCS file cannot be downloaded {} {}".format(
                    item['name'], fcs_file))

input("Press ENTER to exit...")

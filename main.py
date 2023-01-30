import ftplib
import os
import requests
import json
try:
    from charset_normalizer import md__mypyc
except:
    pass

print("Bactoscanner: this tool will analyze the database of a given Bactosense and print out missing files.")
ip_address = "172.16.10.118" #input("IP Address of the Bactosense ").strip()
login = "admin" #input("User name (admin, service) ").strip().lower()
password = "0603"# input("Password ").strip()
#yes = input("Type ENTER after activating the FTP server service on the Bactosense.")
print("Working...")

def get_dirs_ftp(folder=""):
    try:
        contents = ftp.nlst(folder)
    except:
        print("Error for folder {}".format(folder))
        return [], []
    folders = []
    files = []
    for item in contents:
        item = item.strip().replace("\n","").replace("\f","").replace("\\\\", "/").replace(r'\\', r'/')
        if "." not in item:
            folders.append(folder+"/"+item)
        else:
            files.append(os.path.join(folder,item))
    return folders, files

def get_all_dirs_ftp(folder=""):
    dirs = []
    files =[]
    new_dirs = []

    new_dirs, files = get_dirs_ftp(folder)

    while len(new_dirs) > 0:
        for dir in new_dirs:
            dirs.append(dir)

        old_dirs = new_dirs[:]
        new_dirs = []
        for dir in old_dirs:
            n, fil = get_dirs_ftp(dir)
            for new_dir in n:
                new_dirs.append(new_dir)
            for new_file in fil:
                files.append(new_file)

    dirs.sort()
    files.sort()
    return dirs, files


with ftplib.FTP(host=ip_address) as ftp:
    ftp.login(user=login, passwd=password)
    listing, files = get_all_dirs_ftp("")
    
for idx, file in enumerate(files):
    files[idx] = file.replace("\\\\", "/").replace(r'\\', r'/').replace('\\', '/')
    
data = requests.get("http://"+ip_address+"/data", auth=(login,password)).json()
errors = {"fcs_not_found": [], "fcs_corrupt": [], "archive":[]}
for bucket, bucket_content  in data.items():
    if bucket in ["auto", "manual"]:
        for item in bucket_content:
            fcs_file = item['fcsPath'].replace("/archive", "")
            archive_path = item['archivePath'].replace("/archive", "")
            if fcs_file not in files:
                print("ERROR: FCS file not found {} {}".format(item['name'], fcs_file))
                errors["fcs_not_found"].append(fcs_file)
            else:
                try:
                    downloaded_fcs = requests.get("http://"+ip_address+item['fcsUrl'], auth=(login,password))
                    if len(downloaded_fcs.content) < 200:
                        print("ERROR: FCS file too small {} {}".format(item['name'], fcs_file))
                        errors["fcs_corrupt"].append(fcs_file)
                except:
                    print("ERROR: FCS file not found {} {}".format(item['name'], fcs_file))
                    errors["fcs_not_found"].append(fcs_file)
            if archive_path not in listing:
                print("ERROR: wrong archive path {} {}".format(item['name'], archive_path))
                errors["archive"].append(archive_path)
                
json.dump(errors, open("errors.json", "w"), indent=3)
json.dump(data, open("data.json", "w"), indent=3)
json.dump(files, open("files.json", "w"), indent=3)

input("Press ENTER to exit...")
import ftplib
import os
import requests
import calendar
import six
import datetime
import json
try:
    from charset_normalizer import md__mypyc
except:
    pass

print("Bactoscanner 1.1: this tool will analyze the database of a given Bactosense and print out missing or invalid files.")
ip_address = input("IP Address of the Bactosense: ").strip()
login = input("User name (admin, service): ").strip().lower()
password = input("Password: ").strip()
yes = input(
    "Type ENTER after activating the FTP server service on the Bactosense.")
print("Working...")


def load_fcs(path, return_log=True):
    """ Load FCS file, return ndarray and metadata.

    Only the exact output format we use is supported. If any other encoding is
    used, a NotImplementedError is raised.

    :arg bool return_log: if True, return log of events, otherwise return lin value
    :returns: ndarray of data and dictionary of metadata.
    :rtype: np.ndarray, dict.

    Metadata currently contains the timestamp as int, and specimen name as
    string. If the FCS didn't contain a specimen name (SMNO header), the name
    is an empty string.

    """

    with open(path, 'rb') as fo:
        # discard first 10 bytes
        fo.read(10)

        # Get headers
        begin_text = int(fo.read(8))
        end_text = int(fo.read(8))
        begin_data = int(fo.read(8))
        # end_data = int(fo.read(8))

        # Get header section:
        fo.seek(begin_text)
        headers_raw = six.ensure_str(fo.read(end_text - begin_text))

        # Process headers: brake into key/value pairs
        slots = headers_raw[1:].split('/')
        keys, values = slots[::2], slots[1::2]
        keys = [k.strip('$').upper() for k in keys]  # Remove dollar
        headers = dict(list(zip(keys, values)))

        # Panic if the format is not explicitely supported:
        if headers['DATATYPE'] not in ('F', 'I'):
            raise NotImplementedError("DATATYPE '%s' not supported" %
                                      headers['DATATYPE'])
        elif headers['MODE'] != 'L':
            raise NotImplementedError("MODE '%s' not supported" %
                                      headers['MODE'])
        elif headers['BYTEORD'] != '1,2,3,4':
            raise NotImplementedError("BYTEORD '%s' not supported" %
                                      headers['BYTEORD'])

        # Parse parameters:
        dtypes = []
        for i in range(1, int(headers['PAR']) + 1):
            col_name = headers['P%sN' % i]
            # col_range = headers['P%dR' % i]
            encoding_bits = headers['P%sB' % i]
            amplification_factor = headers['P%dE' % i]
            datatype = headers['DATATYPE']

            # Assume linear scale, no amplification
            if amplification_factor.strip() != '0,0':
                raise NotImplementedError("Can't handle parameter P%dE: %s" %
                                          (i, amplification_factor))

            # Convert number of bits to dtype:
            if datatype == 'F' and encoding_bits == '32':
                col_dtype = float
            elif datatype == 'I' and encoding_bits == '32':
                col_dtype = int
            # elif datatype == 'F' and encoding_bits == '64':
                # I could actually handle this case, but I don't have test data
                # col_dtype == np.float64
            else:
                raise NotImplementedError(
                    "64 bit float handling not implemented"
                )

            dtypes.append((col_name, col_dtype))

        # Extract other useful stuff
        if 'DATE' in headers and 'BTIM' in headers:
            date = datetime.datetime.strptime(
                headers['DATE'] + ' ' + headers['BTIM'],
                "%d-%b-%Y %H:%M:%S"
            )
        else:
            date = datetime.datetime.now()
        meta = {'timestamp': calendar.timegm(date.timetuple())}

        if 'SMNO' in headers:
            meta['specimen_name'] = headers['SMNO']
        else:
            meta['specimen_name'] = ''

        if 'VOL' in headers:
            meta['volume'] = float(headers['VOL']) / 1000

        if 'CYT' in headers:
            meta['instrument_id'] = headers['CYT']

        if 'COM' in headers:
            meta['comment'] = headers['COM']

        # Get data section
        fo.seek(begin_data)
        #data_lin = np.fromfile(fo, dtype=dtypes)
        #data_log = log10(data_lin, ignore=['TIME'])

    if return_log:
        return meta, meta
    else:
        return meta, meta



def get_dirs_ftp(folder=""):
    try:
        contents = ftp.nlst(folder)
    except:
        print("Error for folder {}".format(folder))
        return [], []
    folders = []
    files = []
    for item in contents:
        item = item.strip().replace("\n", "").replace(
            "\f", "").replace("\\\\", "/").replace(r'\\', r'/')
        if item.endswith(".png") or item.endswith(".fcs") or item.endswith(".txt.0") or item.endswith(".xlsx") or item.endswith(".pdf") or item.endswith(".db") or item.endswith(".log") or item.endswith(".txt") or item.endswith(".json") or item.endswith(".csv"):
            files.append(os.path.join(folder, item))
        else:
            folders.append(folder+"/"+item)
    return folders, files


def get_all_dirs_ftp(folder=""):
    dirs = []
    files = []
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
    files[idx] = file.replace(
        "\\\\", "/").replace(r'\\', r'/').replace('\\', '/')

has_errors = False
data = requests.get("http://"+ip_address+"/data",
                    auth=(login, password)).json()
errors = {"fcs_not_found": [], "fcs_corrupt": [], "folder_not_found": []}
for bucket, bucket_content in data.items():
    if bucket in ["auto", "manual"]:
        for item in bucket_content:
            fcs_file = item['fcsPath'].replace("/archive", "")
            archive_path = item['archivePath'].replace("/archive", "")
            if fcs_file not in files:
                print("ERROR: FCS file not found {} {}".format(
                    item['name'], fcs_file))
                errors["fcs_not_found"].append(fcs_file)
                has_errors = True
            else:
                try:
                    downloaded_fcs = requests.get(
                        "http://"+ip_address+item['fcsUrl'], auth=(login, password))
                    if len(downloaded_fcs.content) < 200:
                        print("ERROR: FCS file too small {} {}".format(
                            item['name'], fcs_file))
                        errors["fcs_corrupt"].append(fcs_file)
                        has_errors = True
                    try:
                        with open("tmp.fcs", "wb") as f:
                            f.write(downloaded_fcs.content)
                    except Exception as e:
                        print(str(e))
                    try:
                        d, meta = load_fcs("tmp.fcs")
                        if meta is None or d is None:
                            raise Exception("FCS cannot be parsed")
                    except Exception as e:
                        print("ERROR: FCS file is corrupt {} {}".format(
                            item['name'], fcs_file))
                        errors["fcs_corrupt"].append(fcs_file)
                        has_errors = True
                except:
                    print("ERROR: FCS file cannot be downloaded {} {}".format(
                        item['name'], fcs_file))
                    errors["fcs_not_found"].append(fcs_file)
                    has_errors = True
            if archive_path not in listing:
                print("ERROR: wrong archive path {} {}".format(
                    item['name'], archive_path))
                errors["folder_not_found"].append(archive_path)
                has_errors = True

try:
    os.unlink("tmp.fcs")
except:
    pass

ip_address_replaced = ip_address.replace(".", "_")
json.dump(errors, open("{}_errors.json".format(
    ip_address_replaced), "w"), indent=3)
json.dump(data, open("{}_data.json".format(
    ip_address_replaced), "w"), indent=3)
json.dump(files, open("{}_files.json".format(
    ip_address_replaced), "w"), indent=3)

if not has_errors:
    print("No error detected.")
else:
    print("Errors detected.")

input("Press ENTER to exit...")

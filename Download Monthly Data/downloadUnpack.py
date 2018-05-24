import os, sys, urllib2, urllib, time, math
import re
import tarfile



def connect_earthexplorer_no_proxy(account, passwd):
    # mkmitchel (https://github.com/mkmitchell) solved the token issue
    cookies = urllib2.HTTPCookieProcessor()
    opener = urllib2.build_opener(cookies)
    urllib2.install_opener(opener)

    data = urllib2.urlopen("https://ers.cr.usgs.gov").read()
    m = re.search(r'<input .*?name="csrf_token".*?value="(.*?)"', data)
    if m:
        token = m.group(1)
    else:
        print
        "Error : CSRF_Token not found"
        sys.exit(-3)

    params = urllib.urlencode(dict(username=account, password=passwd, csrf_token=token))
    request = urllib2.Request("https://ers.cr.usgs.gov/login", params, headers={})
    f = urllib2.urlopen(request)

    data = f.read()
    f.close()
    if data.find('You must sign in as a registered user to download data or place orders for USGS EROS products') > 0:
        print
        "Authentification failed"
        sys.exit(-1)
    return


def sizeof_fmt(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def downloadChunks(url, nom_fic):
    """ Downloads large files in pieces
     inspired by http://josh.gourneau.com
    """
    try:
        req = urllib2.urlopen(url)
        # if downloaded file is html
        if (req.info().gettype() == 'text/html'):
            print
            "error : file is in html and not an expected binary file"
            lines = req.read()
            if lines.find('Download Not Found') > 0:
                raise TypeError
            else:
                with open("error_output.html", "w") as f:
                    f.write(lines)
                    print
                    "result saved in ./error_output.html"
                    sys.exit(-1)
        # if file too small
        total_size = int(req.info().getheader('Content-Length').strip())
        if (total_size < 50000):
            print
            "Error: The file is too small to be a Landsat Image"
            print
            url
            sys.exit(-1)
        print
        nom_fic, total_size
        total_size_fmt = sizeof_fmt(total_size)

        # download
        downloaded = 0
        CHUNK = 1024 * 1024 * 8
        download_path = 'U:/Fracking Pads'
        with open(download_path + '/' + nom_fic, 'wb') as fp:
            start = time.clock()
            print('Downloading {0} ({1}):'.format(nom_fic, total_size_fmt))
            while True:
                chunk = req.read(CHUNK)
                downloaded += len(chunk)
                done = int(50 * downloaded / total_size)
                sys.stdout.write('\r[{1}{2}]{0:3.0f}% {3}ps'
                                 .format(math.floor((float(downloaded)
                                                     / total_size) * 100),
                                         '=' * done,
                                         ' ' * (50 - done),
                                         sizeof_fmt((downloaded // (time.clock() - start)) / 8)))
                sys.stdout.flush()
                if not chunk: break
                fp.write(chunk)
    except urllib2.HTTPError, e:
        if e.code == 500:
            pass  # File doesn't exist
        else:
            print
            "HTTP Error:", e.code, url
        return False
    except urllib2.URLError, e:
        print
        "URL Error:", e.reason, url
        return False

    return download_path

# TODO: take care of assigning outputdir back in main
def unzipimage(tgzfile, inputdir, outputdir):
    success = 0

    # make a folder in the standard outputdirectory where the unpacked files get stored
    if not os.path.exists("%s/%s" % (outputdir, tgzfile)):
        depositfolder = ("%s/%s" % (outputdir, tgzfile))
        os.makedirs(depositfolder)
        print('created new folder:' + depositfolder)
    if (os.path.exists("%s/%s.tgz" % (inputdir, tgzfile))):
        print
        "\nunzipping..."
        try:
            tar = tarfile.open("%s/%s.tgz" % (inputdir, tgzfile))
            tar.extractall(depositfolder)
            tar.close()
            success = 1
        except tarfile.TarError:
            print'Failed to unzip %s' % tgzfile
        os.remove("%s/%s.tgz" % (inputdir, tgzfile))
    return success, depositfolder


def download_list(req_list, account, passwd, outputdir):
    downloaded_ids = []
    with open(req_list, 'r') as f:
        lines = f.readlines()
        for line in lines:
            prod_name = line
            product = prod_name.strip()
            print product
            if product.startswith('LC8'):
                rep = '4923'
                stations = ['LGN']
            if product.startswith('LE7'):
                rep = '3373'
                # rep='3372"
                stations = ['EDC', 'SGS', 'AGS', 'ASN', 'SG1']
            if product.startswith('LT5'):
                rep = '3119'
                stations = ['GLC', 'ASA', 'KIR', 'MOR', 'KHC', 'PAC', 'KIS', 'CHM', 'LGS', 'MGR', 'COA', 'MPS']
            url = "https://earthexplorer.usgs.gov/download/%s/%s/STANDARD/EE" % (rep, product)
            print 'url=', url
            notfound = False
            try:
                connect_earthexplorer_no_proxy(account, passwd)
                download_path = downloadChunks(url, product + '.tgz')
            except TypeError:
                print
                'product %s not found' % product
                notfound = True
            if notfound != True:
                p, rlocation = unzipimage(product, download_path, outputdir)
                ##send out rlocation to the grass initalizer
                downloaded_ids.append(product)
            else:
                print('scene ' + product + ' not found')
    f.close()
    print downloaded_ids
    return p, rlocation




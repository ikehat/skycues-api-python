# skycues.com
server = "https://skycues.com/v1"
apikey = "5OFz8Vdop86qTzfaFMfxWsM3WMuO3fWGN1LxAp52VQG1jHIjxNgnzf"

# # localhost
# server = "http://localhost/v1"
# apikey = "crVBTYNUIyntybrvtercsGYTHUYHrtefrYGeBTRHEYRTgy7hRHTGDY"

# py skycues-task.py --input <image or geojson file or directory> --output <output file or directory> --date <yyyy-mm-dd> --nirband <yes|no> --clouds <0-100> --mode <details|textures> 
# py skycues-task.py --input D:/Desktop/skycues-sample/test-api-image.tiff --output out --mode details --date 2022-07-15 --clouds 30 --nirband yes

import sys
import os
import requests
import time
requests.packages.urllib3.disable_warnings()

filetoupload = 'test-api-image.png'
payload = {'apikey': apikey}
mergetiles = "false"
georeference = "false"

for param in (" ".join(sys.argv[1:None])).split("--"):
    paramname = param.split(" ")[0]
    paramvalue = " ".join(param.split(" ")[1:None]).strip()

    if (paramname == "input"):
        pathtoupload = paramvalue
    
    if (paramname == "output"):
        output = paramvalue
    
    if (paramname == "clouds"):
        clouds = paramvalue
    
    if (paramname == "mode"):
        mode = paramvalue
    
    if (paramname == "date"):
        date = paramvalue
    
    if (paramname == "nirband"):
        nirband = 'true' if paramvalue.lower() == 'yes' else 'false'
    
    if (paramname == "mergetiles"):
        mergetiles = 'true' if paramvalue.lower() == 'yes' else 'false'
    
    if (paramname == "georeference"):
        georeference = 'true' if paramvalue.lower() == 'yes' else 'false'
    
    if (paramname == "s2bands"):
        s2bands = paramvalue.upper().split(",")

isFile = os.path.isfile(pathtoupload)
payload["s2date"] = date
payload["clouds"] = clouds
payload["nir_band"] = nirband
payload["merge_tiles"] = mergetiles
payload["geo_reference"] = georeference
payload["s2bands"] = s2bands
if mode == "textures":
    payload["mode"] = "v0"
if mode == "details":
    payload["mode"] = "v1"
if mode == "1m":
    payload["mode"] = "v2"


def checkRequest(method, url, data = None):
    try:
        if method == "get":
            response = requests.get(url, verify=False)

        if method == "post":
            response = requests.post(url, data=data, verify=False)
            response = response.json()

        return response

    except Exception as e:
        print("Request FAIL", str(e))

def uploadFile (filetoupload):
    sourcefileextension = filetoupload.split(".")[-1]
    outputfileextension = "tif" if sourcefileextension.lower() in ["geojson","tif","tiff"] else "png"

    if (sourcefileextension == "geojson"):
        mimetype = "application/geo+json"
    elif (sourcefileextension == "tif" or sourcefileextension == "tiff"):
        mimetype = "image/tiff"
    else:
        mimetype = "image/png"

    try:
        files=[('image',(filetoupload,open(filetoupload,'rb'),mimetype))]
        r = requests.post(server+'/order', data=payload, files=files, verify=False)
        uploadresponse = r.json()
        jobid = uploadresponse["jobid"]
        if jobid:
            print("upload image", "Verification PASSED")
        else:
            print("upload image", "Verification FAIL")
    except Exception as e:
        print("upload image", "Request FAIL", str(e))

    creditResponse = checkRequest("post", server+"/check-credit", {"apikey":apikey})
    if creditResponse["credit"] == None or creditResponse["credit"] == 0:
        print("Insuficient credits to order")
        return
    print(creditResponse["credit"], "credits available")
    
    checkOrderResponse = checkRequest("post", server+"/check-order", {"apikey":apikey, "jobid":jobid})
    if checkOrderResponse["ETA"] == None:
        print("Error obtaining the order ETA")
        return
    print("Time remaining:", checkOrderResponse["ETA"])

    # Repeat wait until secondsRemaining are zero
    orderIsReady = False
    while orderIsReady == False:
        loopresponse = checkRequest("post", server+"/check-order", {"apikey":apikey, "jobid":jobid})
        if loopresponse["secondsRemaining"] == 0:
            orderIsReady = True
        else:
            print("Time remaining:", checkOrderResponse["ETA"])
            time.sleep(loopresponse["secondsRemaining"])

    def download():
        img_data = requests.get(server+"/get-order/"+jobid, verify=False).content
        if isFile:
            with open(f"SR-{output}.{outputfileextension}", 'wb') as handler:
                handler.write(img_data)
        else:
            # `${output}/SR-${filetoupload.split("/").slice([-1])[0].split(".").slice(0,-1).join(".")}.png`
            with open(f"""{output}/SR-{".".join(filetoupload.split("/")[-1].split(".")[0:-1])}.{outputfileextension}""", 'wb') as handler:
                handler.write(img_data)
    download()

if (isFile):
    uploadFile(pathtoupload)
else:
    print('isDir')
    if (os.path.isdir(output) == False):
        os.makedirs(output)
    
    for filetoupload in os.listdir(pathtoupload):
        uploadFile(f"{pathtoupload}/{filetoupload}")

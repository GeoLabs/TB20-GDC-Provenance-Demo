# -*- coding: utf-8 -*-
###############################################################################
#  Author:   Gérald Fenoy, gerald.fenoy@geolabs.fr
#  Copyright (c) 2023, GeoLabs SARL. 
############################################################################### 
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
################################################################################
import zoo
import urllib.request
import sys
import json

def route(conf,path,rootUrl):
    cookies=None
    if "HTTP_COOKIE" in conf["renv"]:
        cookies=conf["renv"]["HTTP_COOKIE"]
    if cookies is None:
        req=urllib.request.Request(
                url=rootUrl+(conf["renv"]["REDIRECT_QUERY_STRING"].replace(path+"/","").replace("&","?",1))
                )
    else:
        req=urllib.request.Request(
                url=rootUrl+(conf["renv"]["REDIRECT_QUERY_STRING"].replace(path+"/","").replace("&","?",1)),
                headers={"Cookie": cookies}
                )
    print(rootUrl+(conf["renv"]["REDIRECT_QUERY_STRING"].replace(path+"/","").replace("&","?",1)),file=sys.stderr)
    try:
        response = urllib.request.urlopen(req)
        conf["headers"]["Content-Type"] = response.headers.get_content_type()
        print(conf["headers"]["Content-Type"],file=sys.stderr)
        print(response.headers.keys(),file=sys.stderr)
        if "Set-Cookie" in response.headers.keys():
            conf["headers"]["Set-Cookie"]=response.headers.get("Set-Cookie","")
            conf["renv"]["HTTP_COOKIE"]+="; "+conf["headers"]["Set-Cookie"]
        if conf["headers"]["Content-Type"].count("image")>0 or conf["headers"]["Content-Type"].count("font")>0 or (conf["renv"]["REDIRECT_QUERY_STRING"].count(".js")>0 and conf["renv"]["REDIRECT_QUERY_STRING"].count("openapi.json")==0 and conf["renv"]["REDIRECT_QUERY_STRING"].count("tilejson.json")==0) or conf["renv"]["REDIRECT_QUERY_STRING"].count(".css")>0:
            conf["headers"]["Content-Length"]=response.headers.get("content-length")
            #conf["lenv"]["response"]=str(response.read())
            #conf["lenv"]["response_size"]=response.headers.get("content-length")
            with open(conf["main"]["tmpPath"]+"/"+conf["lenv"]["usid"]+".data", "wb") as binary_file:
                binary_file.write(response.read())
                binary_file.close()
            conf["lenv"]["response_generated_file"]=conf["main"]["tmpPath"]+"/"+conf["lenv"]["usid"]+".data"
        else:
            print("Rewrite ative",file=sys.stderr)
            conf["lenv"]["response"]=response.read().decode("utf-8").replace(conf["osecurity"]["proxyFor"],"/"+conf["openapi"]["rootPath"]+"/stac").replace(conf["osecurity"]["proxyForRaster"],"/"+conf["openapi"]["rootPath"]+"/raster").replace(conf["osecurity"]["proxyForVector"],"/"+conf["openapi"]["rootPath"]+"/vector").replace(conf["osecurity"]["proxyForAuth"],conf["openapi"]["rootHost"]+"/"+conf["openapi"]["rootPath"]+"/authenix").replace("/openapi.json","/"+conf["openapi"]["rootPath"]+"/"+path+"/openapi.json")#.replace("/collections/","/"+conf["openapi"]["rootPath"]+"/"+path+"/collections/").replace("/info","/info?assets=visual")
            print("ok 0 Testing",file=sys.stderr)
            if conf["renv"]["REDIRECT_QUERY_STRING"].count("openapi.json")>0 or conf["renv"]["REDIRECT_QUERY_STRING"].count("/api")>0:
                print("Rewrite openapi",file=sys.stderr)
                conf["lenv"]["response"]=conf["lenv"]["response"].replace("\"/","\"/"+conf["openapi"]["rootPath"]+"/"+path+"/")
                print("\"/"+conf["openapi"]["rootPath"]+"/"+path+"/"+conf["openapi"]["rootPath"]+"/"+path+"/",file=sys.stderr)
                conf["lenv"]["response"]=conf["lenv"]["response"].replace("\"/"+conf["openapi"]["rootPath"]+"/"+path+"/"+conf["openapi"]["rootPath"]+"/"+path+"/","\"/"+conf["openapi"]["rootPath"]+"/"+path+"/")
            if path=="authenix":
                print("Rewrite authenix ative",file=sys.stderr)
                conf["lenv"]["response"]=conf["lenv"]["response"].replace("'/","'/"+conf["openapi"]["rootPath"]+"/"+path+"/")
                conf["lenv"]["response"]=conf["lenv"]["response"].replace(conf["osecurity"]["proxyForAuth1"],conf["openapi"]["rootHost"]+"/"+conf["openapi"]["rootPath"]+"/authenix")
                conf["lenv"]["response"]=conf["lenv"]["response"].replace(conf["osecurity"]["proxyForAuth2"],(conf["openapi"]["rootHost"].replace("https://",""))+"/"+conf["openapi"]["rootPath"]+"/authenix")
                print(conf["lenv"]["response"].count(conf["osecurity"]["proxyForAuth"]),file=sys.stderr)
                print(conf["lenv"]["response"].count(conf["osecurity"]["proxyForAuth1"]),file=sys.stderr)
                #conf["lenv"]["response"]=conf["lenv"]["response"].replace("integrity","initial_integrity")
            conf["lenv"]["response"]=conf["lenv"]["response"].replace("/ogc-api/raster/ogc-api/raster/","/ogc-api/raster/")
            print("ok 1",file=sys.stderr)
    except Exception as e:
        conf["lenv"]["message"]=str(e)
        print("---- ERROR\n",file=sys.stderr)
        print(e,file=sys.stderr)
        print("---- ERROR\n",file=sys.stderr)
        return zoo.SERVICE_FAILED  
    conf["headers"]["status"]="200 OK"
    return zoo.SERVICE_SUCCEEDED

def eoapiRoute(conf,inputs,outputs):
    import sys
    #rootUrl="https://tamn.snapplanet.io"
    zoo.debug(f"eoapiRoute {str(conf['renv'])}")
    rootUrl=conf["osecurity"]["proxyFor"]
    if "REDIRECT_QUERY_STRING" in conf["renv"]:
        zoo.debug("OK query string found")
        if conf["renv"]["REDIRECT_QUERY_STRING"].count("/credentials")>0:
            zoo.debug("credentials")
            try:
                print("credentials",file=sys.stderr)
                f=open(conf["main"]["tmpPath"]+"/openid.json","r")
                print("credentials",file=sys.stderr)
                jsonObject=json.loads(f.read())
                print("credentials",file=sys.stderr)
                jsonObject["id"]="ZOO-Project-secured-access"
                jsonObject["title"]="OpenId Connect Secured Access"
                jsonObject["default_clients"]=[{"id":"ZOO-Secured-Client","grant_types":["implicit","authorization_code+pkce","urn:ietf:params:oauth:grant-type:device_code+pkce"],"redirect_urls":["https://m-mohr.github.io/gdc-web-editor/"]}]
                resultObject={"providers": [jsonObject]}
                print("credentials",file=sys.stderr)
                conf["lenv"]["response"]=json.dumps(resultObject)
                #conf["lenv"]["response_size"]=len(conf["lenv"]["response"])
                conf["headers"]["Content-Type"]="application/json"
                conf["headers"]["Status"]="200 OK"
                print(conf["lenv"]["response"],file=sys.stderr)
            except Exception as e:
                print(e,file=sys.stderr)
        if conf["renv"]["REDIRECT_QUERY_STRING"].count("/me")>0:
            print(conf["lenv"],file=sys.stderr)
            print(conf["auth_env"],file=sys.stderr)
            print(conf["lenv"]["json_user"],file=sys.stderr)
            conf["headers"]["Content-Type"]="application/json"
            conf["headers"]["Status"]="200 OK"
            conf["lenv"]["response"]=conf["lenv"]["json_user"]

        if conf["renv"]["REDIRECT_QUERY_STRING"].count("/raster")>0:
            return route(conf,"raster",conf["osecurity"]["proxyForRaster"])
        if conf["renv"]["REDIRECT_QUERY_STRING"].count("/stac")>0:
            return route(conf,"stac",conf["osecurity"]["proxyFor"])
        if conf["renv"]["REDIRECT_QUERY_STRING"].count("/vector")>0:
            return route(conf,"vector",conf["osecurity"]["proxyForVector"])
        if conf["renv"]["REDIRECT_QUERY_STRING"].count("/authenix")>0:
            return route(conf,"authenix",conf["osecurity"]["proxyForAuth"])
        #if conf["renv"]["REDIRECT_QUERY_STRING"].count("/credentials/oidc")>0:
        #    req=urllib.request.Request(url=conf["osecurity"
    return zoo.SERVICE_SUCCEEDED

def securityOut(conf,inputs,outputs):
    zoo.debug("SECURITY OUT")
    print("SECURITY OUT",file=sys.stderr)
    print(conf["renv"],file=sys.stderr)
    try:
        if len(conf["renv"]["REDIRECT_QUERY_STRING"])==1: #or conf["renv"]["REDIRECT_QUERY_STRING"]=="/conformance":
            print("ok",file=sys.stderr)
            print(conf["openapi"],file=sys.stderr)
            req=urllib.request.Request(
                    conf["openapi"]["rootUrl"]+"/conformance"
                    )
            response = urllib.request.urlopen(req)
            tmpResponseProcessing=response.read().decode("utf-8")
            print(tmpResponseProcessing,file=sys.stderr)
            req=urllib.request.Request(
                    url=conf["osecurity"]["proxyFor"]+"/"
                    )
            print("ok",file=sys.stderr)
            response = urllib.request.urlopen(req)
            print("ok",file=sys.stderr)
            tmpResponse=response.read().decode("utf-8").replace(conf["osecurity"]["proxyFor"],"/"+conf["openapi"]["rootPath"]+"/stac").replace(conf["osecurity"]["proxyForRaster"],"/"+conf["openapi"]["rootPath"]+"/raster").replace(conf["osecurity"]["proxyForVector"],"/"+conf["openapi"]["rootPath"]+"/vector")
            print("ok",file=sys.stderr)
            jsonObjectFetched=json.loads(tmpResponse)
            print("ok",file=sys.stderr)
            jsonObjectResponse=json.loads(conf["lenv"]["json_response_object"])
            jsonObjectProcesses=json.loads(tmpResponseProcessing)
            print("ok",file=sys.stderr)
            for a in range(len(jsonObjectProcesses["conformsTo"])):
                print(jsonObjectProcesses["conformsTo"][a],file=sys.stderr)
                if jsonObjectFetched["conformsTo"].count(jsonObjectProcesses["conformsTo"][a])==0:
                    jsonObjectFetched["conformsTo"]+=[(jsonObjectProcesses["conformsTo"][a])]
            for a in jsonObjectFetched:
                print(a,file=sys.stderr)
                if a=="conformsTo":
                    jsonObjectResponse[a]=jsonObjectFetched[a]
            print("ok",file=sys.stderr)
            jsonObjectResponse["endpoints"]=[
                    {"path":"/credentials/oidc","methods":["GET"]},
                    {"path":"/me","methods":["GET"]},
                    {"path":"/stac/collections","methods":["GET"]},
                    {"path":"/stac/collections/{collection_id}","methods":["GET"]},
                    {"path":"/stac/collections/{collection_id}/items","methods":["GET"]},
                    {"path":"/stac/collections/{collection_id}/items/{item_id}","methods":["GET"]},
                    {"path":"/processes","methods":["GET"]},
                    {"path":"/processes/{process_id}","methods":["GET"]},
                    {"path":"/processes/{process_id}/execution","methods":["POST"]},
                    {"path":"/jobs","methods":["GET"]},
                    {"path":"/jobs/{job_id}","methods":["GET","DELETE"]},
                    {"path":"/jobs/{job_id}/results","methods":["GET"]},
                    ]
            conf["lenv"]["json_response_object"]=json.dumps(jsonObjectResponse)
            return zoo.SERVICE_SUCCEEDED
        elif conf["renv"]["REDIRECT_QUERY_STRING"]=="/conformance":
            jsonObjectResponse=json.loads(conf["lenv"]["json_response_object"])
            req=urllib.request.Request(
                    url=conf["osecurity"]["proxyFor"]+"/"
                    )
            response = urllib.request.urlopen(req)
            tmpResponse=response.read().decode("utf-8").replace(conf["osecurity"]["proxyFor"],"/"+conf["openapi"]["rootPath"]+"/stac").replace(conf["osecurity"]["proxyForRaster"],"/"+conf["openapi"]["rootPath"]+"/raster").replace(conf["osecurity"]["proxyForVector"],"/"+conf["openapi"]["rootPath"]+"/vector")
            jsonObjectFetched=json.loads(tmpResponse)
            for a in jsonObjectFetched:
                if a=="conformsTo":
                    jsonObjectResponse[a]+=jsonObjectFetched[a]
            conf["lenv"]["json_response_object"]=json.dumps(jsonObjectResponse)
            return zoo.SERVICE_SUCCEEDED

    except Exception as e:
        print(e,file=sys.stderr)
        conf["lenv"]["message"]=str(e)
        return zoo.SERVICE_FAILED


    return zoo.SERVICE_SUCCEEDED

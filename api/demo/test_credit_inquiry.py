import requests

EndPoint_China = "gateway.svsbusiness.com"
EndPoint_US = "gateway-us.svsbusiness.com"

if __name__ == '__main__':
    cooperator = "xxxx"
    ace_token = "xxxxxxxxxxxxxxxxxxxxxx"
   
    url = "https://{}/bill/quota/".format(EndPoint_China)
    data_dict = {
        "cooperator": cooperator,
        "ace_token": ace_token
    }
    resp = requests.get(url=url, params=data_dict).text
    print(resp)
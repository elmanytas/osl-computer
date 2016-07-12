# -*- coding: utf-8 -*-
import requests
import json

import time
import re


def get_config(input_file_name):
    input_file = open(input_file_name, 'r')
    for line in input_file:
        if re.match("export", line):
            config[line.split()[1].split("=")[0]] = line.split()[1].split("=")[1].replace('"', '')
    input_file.close()
    #print config

    return config


def get_auth_token(config):

    headers = {}
    headers["Content-Type"] = 'application/json'

    data = """
    {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "name": "%s",
                        "password": "%s",
                        "domain": {
                            "name": "%s"
                        }
                    }
                }
            },
            "scope": {
                "project": {
                    "id": "%s",
                    "domain": {
                        "name": "%s"
                    }
                }
            }
        }
    }
    """ % (config["OS_USERNAME"], config["OS_PASSWORD"], config["OS_USER_DOMAIN_NAME"], config["OS_PROJECT_ID"], config["OS_USER_DOMAIN_NAME"])
    #print data
    headers["Content-Type"] = 'application/json'
    #
    r = requests.post(config["OS_AUTH_URL"] + "/auth/tokens", data=data, headers=headers)
    token = json.loads(r.text)
    token_id = r.headers["X-Subject-Token"]
    #print json.dumps(token, indent=4)
    #print (token_id)

    return (token, token_id)


def get_endpoint(token, endpoint_type, interface_type):
    url = ""
    for i in range(len(token["token"]["catalog"])):
        if (token["token"]["catalog"][i]["type"] == endpoint_type):
            for j in range(len(token["token"]["catalog"][i]["endpoints"])):
                if (token["token"]["catalog"][i]["endpoints"][j]["interface"] == interface_type):
                    url = token["token"]["catalog"][i]["endpoints"][j]["url"]
    return (url)


def create_network(token, token_id, env_name):
    # Redes:
    # - guardamos red con salida pública
    # - creamos red y subred privada
    # - creamos puerto en subred privada
    # - creamos router en subred privada y pública
    # - asignamos puerto a router

    headers = {}
    headers["Content-Type"] = 'application/json'
    headers["X-Auth-Token"] = token_id

    network_url = get_endpoint(token, "network", "public")

    r = requests.get(network_url + "/v2.0/networks", headers=headers)
    #r = requests.post(network_url + "/v2.0/networks", headers=headers, data=data)
    #print r.text
    networks = json.loads(r.text)
    #print json.dumps(networks, indent=4)
    # # Obtenemos el network_id de la red de publica
    public_network = {}
    for network in networks["networks"]:
        if network["router:external"]:
            public_network = network
    print ((json.dumps(public_network, indent=4)))
    # public_network_id = pretty_response["network"]["id"]

    # Creamos la red de la instancia
    private_net_name = env_name + "_net"
    data = """
    {
        "network": {
            "name": "%s",
            "admin_state_up": true
        }
    }
    """ % private_net_name
    r = requests.post(network_url + "/v2.0/networks", headers=headers, data=data)
    private_net = json.loads(r.text)
    print ((json.dumps(private_net, indent=4)))
    # Creamos la subred de la instancia
    # subnetwork_url = "http://openstack.paradigmadigital.com:9696/v2.0/subnets"
    private_subnet_name = env_name + "_subnet"
    data = """
    {
     "subnet": {
         "name": "%s",
         "ip_version": 4,
         "network_id": "%s",
         "cidr": "172.17.235.0/24",
         "gateway_ip": "172.17.235.1",
         "allocation_pools": [
             {
                 "start": "172.17.235.10",
                 "end": "172.17.235.100"
             }
         ],
         "enable_dhcp": "true"
     }
    }
    """ % (private_subnet_name, private_net["network"]["id"])
    r = requests.post(network_url + "/v2.0/subnets", headers=headers, data=data)
    private_subnet = json.loads(r.text)
    print ((json.dumps(private_subnet, indent=4)))

    # Creamos un router para dar salida a la red publica hacia el exterior
    # routers_url = "http://openstack.paradigmadigital.com:9696/v2.0/routers"
    router_name = env_name + "_router"
    data = """
    {
        "router": {
            "name": "%s",
            "external_gateway_info": {
                "network_id": "%s"
            }
        }
    }
    """ % (router_name, public_network["id"])
    r = requests.post(network_url + "/v2.0/routers", headers=headers, data=data)
    external_router = json.loads(r.text)
    print ((json.dumps(external_router, indent=4)))

    # Conectamos el router público con la red privada
    # add_router_interface_url = routers_url + "/" + external_router_id + "/add_router_interface"
    data = """
    {
        "subnet_id": "%s"
    }
    """ % private_subnet["subnet"]["id"]
    r = requests.put(network_url + "/v2.0/routers/" + external_router["router"]["id"] + "/add_router_interface", headers=headers, data=data)
    external_router_connections = json.loads(r.text)
    print ((json.dumps(external_router_connections, indent=4)))

    network_env = {}
    network_env["public"] = public_network
    network_env["private_net"] = private_net["network"]
    network_env["private_subnet"] = private_subnet["subnet"]
    network_env["external_router"] = external_router["router"]
    return (network_env)


def create_computer(token, token_id, env):
    server_env = {}
    headers = {}
    headers["Content-Type"] = 'application/json'
    headers["X-Auth-Token"] = token_id

    #print ((json.dumps(token, indent=4)))
    name = env["name"] + "_computer"
    #image = "a9f3ef90-da4f-47f4-b05a-c8180b3bda60"
    image = "78eb8e56-d6b5-424d-9a94-f92e02c498f7"
    flavor = "2"
    #print ((json.dumps(env, indent=4)))
    data = """
    {
        "server" : {
            "name" : "%s",
            "imageRef" : "%s",
            "flavorRef" : "%s",
            "availability_zone": "nova",
            "security_groups": [
                {
                    "name": "default"
                }
            ],
            "networks": [
                {
                    "uuid": "%s"
                }
            ]
        }
    }
    """ % (name, image, flavor, env["network"]["private_net"]["id"])
    compute_url = get_endpoint(token, "compute", "public")
    r = requests.post(compute_url + "/servers", headers=headers, data=data)
    #print (r.text)
    server_env = json.loads(r.text)
    #network_url = get_endpoint(token, "network", "public")
    #print ((json.dumps(server_env, indent=4)))

    return (server_env["server"])


def get_console(token, token_id, server):
    headers = {}
    headers["Content-Type"] = 'application/json'
    headers["X-Auth-Token"] = token_id
    data = """
    {
        "os-getVNCConsole": {
            "type": "novnc"
        }
    }
    """
    #data = """
    #{
        #"os-getSPICEConsole": {
            #"type": "spice-html5"
        #}
    #}
    #"""
    compute_url = get_endpoint(token, "compute", "public")
    r = requests.post(compute_url + "/servers/" + server["id"] + "/action", headers=headers, data=data)
    print ((r.text))
    console_env = json.loads(r.text)
    print ((json.dumps(console_env, indent=4)))

    return (console_env["console"])


env = {}
env["name"] = "prueba"
# Load config from origin
config = {}
config = get_config("admin-openrc.sh")
token, token_id = get_auth_token(config)
# # Actualizamos las cabeceras con el token recién obtenido

#env["network"] = create_network(token, token_id, env["name"])

#print ((json.dumps(env, indent=4)))
#env["server"] = create_computer(token, token_id, env)
#print ((json.dumps(env, indent=4)))

#time.sleep(10)
#env["console"] = get_console(token, token_id, env["server"])

print ((json.dumps(env, indent=4)))
print token_id
#print ((env["console"]["url"]))


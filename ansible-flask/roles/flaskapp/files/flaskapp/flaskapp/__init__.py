# -*- coding: UTF-8 -*-
from flask import Flask
from flask import request
from flask import json

import requests

app = Flask(__name__)


# http://blog.luisrei.com/articles/flaskrest.html
@app.route('/oslh2b', methods=['POST'])
def oslh2b():
    if request.method == 'POST':
        json_headers = request.headers
        data = json.loads(request.data)

        destination_url = data["destination_url"]
        data.pop("destination_url", None)
        json_data = json.dumps(data)

        r = requests.post(destination_url, data=json_data, headers=json_headers)
        data = {}
        data["body"] = json.loads(r.text)
        data["headers"] = r.headers

        return str(data)


def config2dict(request_data):
    '''
    Convert a lot of lines with two strings per line in a dictionary
    OS_AUTH_URL http://openstack-vcenter:5000/v3
    OS_PROJECT_ID 9d7812704e104a208603c5d0481bd952
    OS_PROJECT_NAME admin
    OS_USER_DOMAIN_NAME default
    OS_USERNAME admin
    OS_PASSWORD admin
    OS_REGION_NAME RegionOne
    name prueba
    '''
    configuration = {}
    for line in request_data.splitlines():
        if len(line.split()) == 2:
            configuration[line.split()[0]] = line.split()[1]

    return(configuration)


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
    """ % (config["OS_USERNAME"],
           config["OS_PASSWORD"],
           config["OS_USER_DOMAIN_NAME"],
           config["OS_PROJECT_ID"],
           config["OS_USER_DOMAIN_NAME"])
    #print data
    headers["Content-Type"] = 'application/json'
    #
    r = requests.post(config["OS_AUTH_URL"] + "/auth/tokens",
                      data=data, headers=headers)
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

    network_url = get_endpoint(token, "network", "public")

    headers = {}
    headers["Content-Type"] = 'application/json'
    headers["X-Auth-Token"] = token_id

    r = requests.get(network_url + "/v2.0/networks", headers=headers)
    #r = requests.post(network_url + "/v2.0/networks",headers=headers,data=data)
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
    r = requests.post(network_url + "/v2.0/networks",
                      headers=headers, data=data)
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
    # add_router_interface_url = routers_url + "/" + external_router_id +
    # "/add_router_interface"
    data = """
    {
        "subnet_id": "%s"
    }
    """ % private_subnet["subnet"]["id"]
    r = requests.put(network_url + "/v2.0/routers/" + external_router["router"]["id"] + "/add_router_interface",
                     headers=headers, data=data)
    external_router_connections = json.loads(r.text)
    print ((json.dumps(external_router_connections, indent=4)))

    network_env = {}
    network_env["public"] = public_network
    network_env["private_net"] = private_net["network"]
    network_env["private_subnet"] = private_subnet["subnet"]
    network_env["external_router"] = external_router["router"]
    return (network_env)


def create_server(token, token_id, env):
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


def dict2config(dictio):
    config = ""
    for key in list(dictio.keys()):
        config = config + str(key) + " " + str(dictio[key]) + "\n"

    return (config)


@app.route('/create_computer_mock', methods=['POST'])
def create_computer_mock():
    data = """
router_id 647a4c8f-f055-461d-bd91-b7c224f4acd9
server_id 00633113-acfc-41fc-8b23-88d2e84c1a90
name prueba
OS_USERNAME admin
subnet_id ca2cfacb-de0a-4705-a334-9a4cbb709f41
OS_PROJECT_ID 9d7812704e104a208603c5d0481bd952
OS_REGION_NAME RegionOne
OS_USER_DOMAIN_NAME default
OS_AUTH_URL http://openstack-vcenter:5000/v3
OS_PROJECT_NAME admin
OS_PASSWORD admin
net_id bee1007e-1289-4c75-9dd5-dbe11a3fdba5
"""
    return (data)


@app.route('/create_computer', methods=['POST'])
def create_computer():
    '''
    create_computer
    This creates a server and returns a list of net_id, subnet_id, router_id,
    server_id and console_url.
    Console url can be configured in a media prim.
    The other data can be used to delete the server.
    '''
    if request.method == 'POST':
        env = {}

        config = {}
        config = config2dict(request.data)
        env["name"] = config["name"]
        token, token_id = get_auth_token(config)

        env["network"] = create_network(token, token_id, env["name"])
        config["net_id"] = env["network"]["private_net"]["id"]
        config["router_id"] = env["network"]["external_router"]["id"]
        config["subnet_id"] = env["network"]["private_subnet"]["id"]

        env["server"] = create_server(token, token_id, env)
        config["server_id"] = env["server"]["id"]

    return dict2config(config)


def delete_server(token, token_id, server_id):
    headers = {}
    headers["Content-Type"] = 'application/json'
    headers["X-Auth-Token"] = token_id

    compute_url = get_endpoint(token, "compute", "public")
    requests.delete(compute_url + "/servers/" + server_id, headers=headers)

    return


def delete_network(token, token_id, net_id, subnet_id, router_id):
    headers = {}
    headers["Content-Type"] = 'application/json'
    headers["X-Auth-Token"] = token_id

    network_url = get_endpoint(token, "network", "public")

    #r = requests.put(network_url + "/v2.0/routers/" + external_router["router"]["id"] + "/add_router_interface",
                     #headers=headers, data=data)
    #r = requests.post(network_url + "/v2.0/routers", headers=headers, data=data)
    #r = requests.post(network_url + "/v2.0/subnets", headers=headers, data=data)
    return


@app.route('/delete_computer', methods=['POST'])
def delete_computer():
    '''
    delete_computer
    This deletes a computer and returns 200 if ok
    '''
    if request.method == 'POST':
        config = {}
        config = config2dict(request.data)

        token, token_id = get_auth_token(config)
        delete_server(token, token_id, config["server_id"])
        delete_network(token, token_id,
                       config["net_id"], config["subnet_id"],
                       config["router_id"])


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
    r = requests.post(compute_url + "/servers/" + server["id"] + "/action",
                      headers=headers, data=data)
    print ((r.text))
    console_env = json.loads(r.text)
    print ((json.dumps(console_env, indent=4)))

    return (console_env["console"])


@app.route('/get_console_url', methods=['POST'])
def get_console_url():
    if request.method == 'POST':
        env = {}

        config = {}
        config = config2dict(request.data)
        env["name"] = config["name"]
        token, token_id = get_auth_token(config)

        env["server"] = {}
        env["server"]["id"] = config["server_id"]
        env["console"] = get_console(token, token_id, env["server"])

    return ("console_url " + env["console"]["url"])


if __name__ == '__main__':
    app.run()

key http_request_id;
string os_user = "admin";
string os_password = "admin";

default
{
    state_entry()
    {
        llSay(0, "Script running");
    }
    touch_end(integer num_detected)
    {
        llSay(0, "tocado");
        string data = "
        {
            \"auth\": {
                \"identity\": {
                    \"methods\": [
                        \"password\"
                    ],
                    \"password\": {
                        \"user\": {
                            \"name\": \"admin\",
                            \"password\": \"admin\",
                            \"domain\": {
                                \"name\": \"default\"
                            }
                        }
                    }
                },
                \"scope\": {
                    \"project\": {
                        \"id\": \"9d7812704e104a208603c5d0481bd952\",
                        \"domain\": {
                            \"name\": \"default\"
                        }
                    }
                }
            }
        }";
        http_request_id = llHTTPRequest("http://openstack-vcenter:5000/v3/auth/tokens", [HTTP_METHOD, "POST", HTTP_MIMETYPE, "application/json"], data);
    }

    http_response(key request_id, integer status, list metadata, string body)
    {
        if (request_id != http_request_id) return;// exit if unknown
 
        vector COLOR_BLUE = <0.0, 0.0, 1.0>;
        float  OPAQUE     = 1.0;
        string header = llGetHTTPHeader(request_id, "x-subject-token");
        llSetText("header: " + header + "\nbody: " + body, COLOR_BLUE, OPAQUE);
    }
}
state create_network {
    state_entry()
    {
        llSay(0, "in create_network");
    }
}

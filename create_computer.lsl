key http_request_id;
string os_user = "admin";
string os_password = "admin";
string openrc_notecard = "openrc_notecard";

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
            \"destination_url\" : \"http://openstack-vcenter.fermosit.es:5000/v3/auth/tokens\",
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
                        \"id\": \"3abfcf8f663f47119dc79b046cef8071\",
                        \"domain\": {
                            \"name\": \"default\"
                        }
                    }
                }
            }
        }";
//        http_request_id = llHTTPRequest("http://openstack-vcenter.fermosit.es:5000/v3/auth/tokens", [HTTP_METHOD, "POST", HTTP_MIMETYPE, "application/json"], data);
        http_request_id = llHTTPRequest("http://10.42.84.201/oslh2b", [HTTP_METHOD, "POST", HTTP_MIMETYPE, "application/json"], data);
    }

    http_response(key request_id, integer status, list metadata, string body)
    {
        if (request_id != http_request_id) return;// exit if unknown

        vector COLOR_BLUE = <0.0, 0.0, 1.0>;
        float  OPAQUE     = 1.0;
        //llSetText("metadata: " + (string)metadata, COLOR_BLUE, OPAQUE);
        llSetText( "status: " + (string)status + "\nbody: " + body, COLOR_BLUE, OPAQUE);
    }
}
state create_network {
    state_entry()
    {
        llSay(0, "in create_network");
    }
}
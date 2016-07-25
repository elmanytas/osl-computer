key notecardQueryId;
// script-wise, the first notecard line is line 0, the second line is line 1, etc.
integer notecardLine;

string notecardName = "openrc_notecard";


key http_request_id;


// Set of functions that allow to use a dicionary of strings in lsl
list configuration_dict = [];
integer get_key_pos(string search_key, list dictionary) {
    // Returns key position in the array.
    // This is a private dictionary function.
    integer key_pos = -1;
    integer length = 0;
    length = llGetListLength(dictionary);

    integer i = 0;
    integer found = 0;
    while (((i*2) < length) && (found == 0)) {
        if (search_key == llList2String(dictionary, i*2)) {
            found = 1;
            key_pos = i*2;
        } else {
            i++;
        }
    }
    return (key_pos);
}

string get_value(string search_key, list dictionary) {
    string search_value = "";
    integer key_pos = get_key_pos(search_key, dictionary);

    if (key_pos >= 0) {
        search_value = llList2String(dictionary, (key_pos+1));
    }

    return (search_value);
}

list set_value(string key_to_insert, string value_to_insert, list dictionary) {
    list newDictionary = dictionary;
    integer key_pos = get_key_pos(key_to_insert, dictionary);

    if (key_pos >= 0) {
        newDictionary = llListReplaceList(newDictionary, [value_to_insert], key_pos, key_pos);
    } else {
        newDictionary = newDictionary + [key_to_insert, value_to_insert];
    }
    return (newDictionary);
}

say_dict(list dictionary) {
    integer length = 0;
    length = llGetListLength(dictionary);

    integer i = 0;
    llOwnerSay("{");
    while ((i*2) < length) {
        llOwnerSay("    \""+llList2String(dictionary, i*2)+"\": \""+llList2String(dictionary, (i*2)+1)+"\",");
        i++;
    }
    llOwnerSay("}");

}
list get_keys(list dictionary) {
    list key_list= [];

    integer length = 0;
    length = llGetListLength(dictionary);

    integer i = 0;
    while ((i*2) < length) {
        key_list=key_list + [llList2String(dictionary, i*2)];
        i++;
    }
    return (key_list);
}
/*
list delete_key(string key_to_delete, list dictionary) {
}
*/
 // End dictionary functions

default
{
    state_entry()
    {
        integer length = 0;
        llSay(0, "Script running");
        length = llGetListLength(configuration_dict);
        if (length == 0) {
            llOwnerSay("Loading configuration");
            state load_config;
        } else {
            llOwnerSay("Configuration loaded");
            llOwnerSay(get_value("name", configuration_dict));

        }
    }

    touch_end(integer num_detected)
    {
        list key_list = get_keys(configuration_dict);
        llOwnerSay((string)key_list);

        string data = "";
        integer i = 0;
        integer length = llGetListLength(key_list);
        while (i<=length) {
            data = data + llList2String(key_list, i) + " " + get_value(llList2String(key_list, i), configuration_dict);
            llOwnerSay(llList2String(key_list, i));
            i++;
            if (i<=length) {
                data = data + "\n";
            }
        }

        llOwnerSay(data);

        http_request_id = llHTTPRequest("http://10.42.84.201/create_computer", [HTTP_METHOD, "POST", HTTP_MIMETYPE, "application/json"], data);
    }


    http_response(key request_id, integer status, list metadata, string body)
    {
        if (request_id != http_request_id) return;// exit if unknown
        vector COLOR_BLUE = <0.0, 0.0, 1.0>;
        float  OPAQUE     = 1.0;
        //llSetText("metadata: " + (string)metadata, COLOR_BLUE, OPAQUE);
        llSetText( "statusssss: " + (string)status + "\nbody: " + body, COLOR_BLUE, OPAQUE);
    }
}
state load_config {
    state_entry()
    {
        llSay(0, "in load_config");
        // Check the notecard exists, and has been saved
        if (llGetInventoryKey(notecardName) == NULL_KEY)
        {
            llOwnerSay( "Notecard '" + notecardName + "' missing or unwritten");
            return;
        }
        // say("reading notecard named '" + notecardName + "'.");
        notecardQueryId = llGetNotecardLine(notecardName, notecardLine);
    }

    dataserver(key query_id, string data)
    {
        if (query_id == notecardQueryId)
        {
            if (data == EOF) {
                llOwnerSay("Done reading notecard, read " + (string) notecardLine + " notecard lines.");
                state default;
            }
            else
            {
                // bump line number for reporting purposes and in preparation for reading next line
                ++notecardLine;
                list clave = llParseString2List(data, [" "], []);
                configuration_dict = set_value(llList2String(clave, 0), llList2String(clave, 1), configuration_dict);
                //llOwnerSay((string)configuration_values);
                //llOwnerSay( "Line: " + (string) notecardLine + " " + data);
                notecardQueryId = llGetNotecardLine(notecardName, notecardLine);
            }
        }
    }
}

# osl-computer
OpenSim/SecondLife inworld computer

## Description
Create a computer inside OpenSim/SecondLife using the OpenStack api to create an instance, and get the console url.
Then, set the url to a media face on a prim.

## More detailed description
When a computer object is rezzed in world (on_rez) the computer screen:
- ask for an auth token to OpenStack
- creates a private network
- creates a private router
- creates a server
- gets console url
- sets the face 1 to the media url
- remember to the user via chat to enable media

## Problems
### Cannot receive headers in rest calls
Looks like after a http_request event only body can be obtained.
There is no way to read returned headers but the authentication token id is in x-subject-token .

### Json problems
I cannot parse json answers!
* In Second Life: http://wiki.secondlife.com/wiki/Json_usage_in_LSL
* In OpenSim there is a different (and better) implementation to parse json files: http://opensimulator.org/wiki/JsonStore_Module
So writing a rest client in lsl is not the same in OpenSim and Second Life and the JsonStore module is disabled by default in OpenSim.


## Final architecture
Use OpenSim/Second Life as little as possible to interact with external services.
All logic is implemented in the flask app and use the OpenSim/Second Life Object to store results returned as simple csv strings.

Architecture:
* FrontEnd: OpenSim/Second Life stores Object information.
* FackEnd (FrontEnd of the Backend): Flask App receives calls from FrontEnd, modify and resend to OpenStack. Then returns a simple string easy to par$
* Backend: Receives FackEnd calls and does the final tasks.

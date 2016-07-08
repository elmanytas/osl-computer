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

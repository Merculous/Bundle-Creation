# prerequisites

asrpatch: https://github.com/cfw-project/asr_patcher-2  
dmg: xpwn  
hdutil: xpwn  
iBoot32Patcher: https://github.com/Merculous/iBoot32Patcher  
xpwntool: xpwn  
7zip: this is for getting the mount name for the rootfs

Put the binaries or symlink inside a folder called 'bin' (it must be inside this projects folder)

inside a virtual environment, I used `venv`, so I use `python3 -m venv venv`  
	- to enter the virtual environment, run `. venv/bin/activate`  
	- then run `pip install pipenv`  
	- then run `pipenv install`  

once you have installed the required libraries for python, move to the next setup below

# setting up bin folder
compile xpwn: https://github.com/Merculous/xpwn  
	- clone my fork as it contains a necessary compile flag to complie xpwn completely  
	- to make compiling easy, use the `make package` command to make xpwn and create a bzip2 compressed tar  
	- put the required binaries from xpwn mentioned above to wherever you want, I put mine in `/usr/local/bin`, although it doesn't matter where you put them, just make sure they're in the `bin` folder where this project was cloned

compile iBoot32Patcher:  
	- just a simple `make` is all you need to do, and then as I said above, copy/move/symlink to `bin`

download asrpatch:  
	- put inside `bin`

download 7zip  
	- Nothing else required here

# getting keys
Go to https://theiphonewiki.com and get whatever keys you want, but DO NOT SKIP AHEAD OF ME  
	- When you're on the page with your keys, if you haven't already, download the ipsw, and then click the `view source` button, this is where the key template is stored which is used by my script  
	- Copy everything in the middle starting with `{{keys` and ending with `}}`, then put this inside a file


# creating bundles
All you need to do is run `./tool --ipsw "your ipsw here" --template "your file with the keys"`

# after bundle creation
Your bundle will be inside `bundles`, everything that you need to have a barebones custom ipsw will be inside the bundle corresponding to the ipsw you had provided

# automatic ipsw creation
Some reason xpwn makes ipsw's in a way that messes up booting, at least in my case, so I may have to add code in this project, or inside my other project pyXpwn that'll make use of this code to make a proper custom ipsw, but that'll be done soon, I'll have to make up my mind on how I want to do this

# prerequisites

asrpatch: https://github.com/cfw-project/asr_patcher-2  
dmg: xpwn  
hdutil: xpwn  
iBoot32Patcher: https://github.com/Merculous/iBoot32Patcher  
xpwntool: xpwn  
7zip: this is for getting the mount name for the rootfs  
fuzzy_patcher: https://github.com/Merculous/ios-jb-tools

Put the binaries or symlink inside a folder called `bin` (it must be inside this projects folder)

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

compile fuzzy_patcher: https://github.com/Merculous/ios-jb-tools  
	- run `make` inside `tools_src/fuzzy_patcher`

# creating bundles
Before running: Make sure your device is connected to the internet  
this is to get the keys for your specified ipsw

All you need to do is run `./tool --ipsw "your ipsw here"`

# after bundle creation
Your bundle will be inside `bundles`, everything that you need to have a barebones custom ipsw will be inside the bundle corresponding to the ipsw you had provided

# automatic ipsw creation
As of commit 8eeb3a37e896f9d096a09b5441037451fa9f562e, custom ipsw's are now being made. The custom ipsw is inside the same folder, named `custom.ipsw`

# restoring

Use https://github.com/Merculous/idevicerestore with `-c` for restoring with a custom ipsw. I had removed the lines that try to use limera1n, though ipwndfu is much better at doing DFU stuff than idevicerestore


# NOTES

As of May 18 and commit 8d49469965108657f1321b5e0692fcddcda6e4dd, which is today as I'm making this, I now at least know that ASR gets killed, so I need to figure out what went wrong.  

The kernel MUST be patched, I'm not sure exactly what patches are needed but sn0wbreeze kernels  
contain the patches needed to restore successfully. I will try to figure out what patches are  
needed in order to not get this error below.  


entering update_iBoot  
write_image3_data: flashing LLB data (length = 0x241d0)  
AppleImage3NORAccess::_getSuperBlock imageVersion: 3  
0: RamrodErrorDomain/3e9: update_iBoot: error writing LLB image  
1: NSMachErrorDomain/e00002e2: write_image3_data: AppleImage3NORAccess returned an error when writing image3 object

# ipwndfu

Use commit 0da9adbe2aa40a06769a450d9ae1d2383d2e8be0 (right before checkm8 addition)

Some reason alloc8 is broken with the latest commit.

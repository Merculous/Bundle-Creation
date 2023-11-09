# prerequisites

dmg: xpwn \
hdutil: xpwn \
iBoot32Patcher: https://github.com/Merculous/iBoot32Patcher \
xpwntool: xpwn \
7zip: this is for getting the mount name for the rootfs \
ldid: https://github.com/ProcursusTeam/ldid

Put the binaries or symlink inside a folder called `bin` (it must be inside this projects folder)

inside a virtual environment, I used `venv`, so I use `python3 -m venv venv`

- to enter the virtual environment, run `. venv/bin/activate`
- then run `pip install poetry`
- then run `poetry install`

once you have installed the required libraries for python, move to the next setup below

# setting up bin folder

compile xpwn: https://github.com/Merculous/xpwn

- clone my fork as it contains a necessary compile flag to complie xpwn completely
- to make compiling easy, use the `make package` command to make xpwn and create a bzip2 compressed tar
- put the required binaries from xpwn mentioned above to wherever you want, I put mine in `/usr/local/bin`, although it doesn't matter where you put them, just make sure they're in the `bin` folder where this project was cloned

compile iBoot32Patcher:

- just a simple `make` is all you need to do, and then as I said above, copy/move/symlink to `bin`

download 7zip

- put inside `bin`

compile ldid

- `make` and then `sudo make install`, then copy/move/symlink to `bin`

# creating bundles

Before running, make sure your device is connected to the internet.
This is to get the keys for your specified ipsw

All you need to do is run `./tool --ipsw "your ipsw here"` to make a
bundle. If you also want to make a ipsw, just add `--make`

# after bundle creation

Your bundle will be inside `bundles`, everything that you need to have a barebones custom ipsw will be inside the bundle corresponding to the ipsw you had provided, except ramdisk patches.

I only have ramdisk patches added when `--make` is specified. I need
to do more testing to incorporate ramdisk patches to work exactly how
xpwn would expect them

# restoring

Use https://github.com/Merculous/idevicerestore with `-c` for restoring with a custom ipsw. I had removed the lines that try to use limera1n, though ipwndfu is much better at doing DFU stuff than idevicerestore

# NOTES

- The kernel MUST be patched
- iOS 6+ requires restored_external to be patched. Simply patch the branch to _ramrod_ticket_update

The error below is definitely tied to restored_external but I also believe some versions also check this in the kernel

entering update_iBoot  
write_image3_data: flashing LLB data (length = 0x241d0)  
AppleImage3NORAccess::\_getSuperBlock imageVersion: 3  
0: RamrodErrorDomain/3e9: update_iBoot: error writing LLB image  
1: NSMachErrorDomain/e00002e2: write_image3_data: AppleImage3NORAccess returned an error when writing image3 object

# ipwndfu

Use commit 0da9adbe2aa40a06769a450d9ae1d2383d2e8be0 (right before checkm8 addition)

Some reason alloc8 is broken with the latest commit.

# Credits

Do not associate ordering with varied importance, they all are important equally.

axi0mX https://twitter.com/axi0mX - ipwndfu

pimskeks https://twitter.com/pimskeks - idevicerestore

planetbeing https://twitter.com/planetbeing - xpwn

iH8sn0w https://twitter.com/iH8sn0w - iBoot32Patcher, kernel patches, sn0wbreeze

And everyone else who's contributed information about doing this kind of work. You all
are amazing people. If you know if contributed in making this work public, thank you!

# Tested

iPhone2,1

    - 4.3.x: Tested and fully working

    - 5.x: Tested and fully working

    - 6.x: Tested and fully working

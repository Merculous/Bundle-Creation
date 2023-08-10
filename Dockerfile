
FROM ubuntu

RUN apt update

RUN cd

RUN apt -y install git cmake g++ clang zlib1g-dev libssl-dev libbz2-dev libpng-dev libminizip-dev libboost-program-options-dev libboost-iostreams-dev p7zip-full

RUN git clone https://github.com/Merculous/xpwn
RUN cd xpwn && mkdir build && cd build && cmake .. && make dmg-bin xpwntool && cp dmg/dmg ipsw-patch/xpwntool /usr/local/bin
RUN cd

RUN git clone https://github.com/Merculous/iBoot32Patcher
RUN cd iBoot32Patcher && make && cp iBoot32Patcher /usr/local/bin
RUN cd

RUN git clone https://github.com/Merculous/ios-jb-tools
RUN cd ios-jb-tools/tools_src/fuzzy_patcher && make && cp fuzzy_patcher /usr/local/bin
RUN cd

RUN rm -rf xpwn iBoot32Patcher ios-jb-tools

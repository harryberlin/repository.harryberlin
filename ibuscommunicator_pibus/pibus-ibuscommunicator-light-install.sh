#!/bin/bash

install_autostart() {
	if [ "$OSMC" -eq "1" ]; then
		sudo apt-get -y install cron psmisc
		if [ $? != "0" ]; then
			exit 3
		fi
		sudo crontab -l | grep pibus > /dev/null
		if [ $? != "0" ]; then
			sudo crontab <<EOF
@reboot ${HOMEDIR}/pibus ${FLAGS}
EOF
		else
			echo -e "crontab already contains pibus - \033[31mskipping\033[m"
		fi

	else
		# OpenELEC
		grep pibus ${HOMEDIR}/.config/autostart.sh > /dev/null
		if [ $? != "0" ]; then
			echo "${HOMEDIR}/pibus ${FLAGS} &" >> ${HOMEDIR}/.config/autostart.sh
		else
			echo -e "autostart.sh already contains pibus - \033[31mskipping\033[m"
		fi
		chmod +x ${HOMEDIR}/.config/autostart.sh
	fi
}

install_pibus() {
	rm -f pibus-latest.zip
	wget http://pibus.info/sw/pibus-latest.zip
	if [ $? != "0" ]; then
		echo -e "\033[31mDownload failed. Connected to the internet?\033[m"
		exit 1
	fi
	if [ "$OSMC" -eq "1" ]; then
		sudo killall pibus
	else
		killall pibus
	fi
	unzip -o pibus-latest.zip pibus
	chmod +x ${HOMEDIR}/pibus
}

choose_skin() {
	while true; do
		echo
		echo -e "\033[32m1) \033[mskin.pibus"
		echo -e "\033[32mn) \033[mnone"
		echo -e -n "\033[1;35mSelect skin to download:\033[m"
		read -r line
		if [ $? -eq 0 ]; then
			case $line in
				"1")
					SKIN_NAME="skin.pibus"
					SKIN_URL="http://pibus.info/sw/skins/skin.pibus-latest.zip"
					SKIN_FILE="skin.pibus-latest.zip"
					SKIN_UNPACK="unzip"
					return 0
					;;
				"n")
					SKIN_NAME=""
					return 1
					;;
			esac
		fi
	done
}

install_skin() {
	choose_skin
	if [ $? -eq 0 ]; then
		rm -f ${SKIN_FILE}
		wget ${SKIN_URL}
		# I don't know how to automatically install it :(
	fi
}

append_to_configtxt() {
	echo "adding $1 to config.txt"
	if [ "$OSMC" -eq "1" ]; then
		echo "dtoverlay=$1" | sudo tee --append ${CONFIGDIR}/config.txt
	else
		mount -o remount,rw ${CONFIGDIR}
		echo "dtoverlay=$1" >> ${CONFIGDIR}/config.txt
		mount -o remount,ro ${CONFIGDIR}
	fi
}

install_dac_overlay() {
	grep "^dtoverlay=hifiberry-dac" ${CONFIGDIR}/config.txt > /dev/null
	if [ $? != "0" ]; then
		append_to_configtxt "hifiberry-dac"
	else
		echo -e "DAC already configured in config.txt - \033[31mskipping\033[m"
	fi
}

install_pi3_overlay() {
	dmesg | grep "Raspberry.Pi.3"
	if [ $? -eq 0 ]; then
		grep "^dtoverlay=pi3-miniuart-bt" ${CONFIGDIR}/config.txt > /dev/null
		if [ $? != "0" ]; then
			append_to_configtxt "pi3-miniuart-bt"
			# OpenELEC might be missing this overlay file
			if [ ! -e "${CONFIGDIR}/overlays/pi3-miniuart-bt-overlay.dtbo" ]; then
				if [ ! -e "${CONFIGDIR}/overlays/pi3-miniuart-bt-overlay.dtb" ]; then
					mount -o remount,rw ${CONFIGDIR}
					wget -P ${CONFIGDIR}/overlays/ http://pibus.info/sw/pi3-miniuart-bt-overlay.dtb
					mount -o remount,ro ${CONFIGDIR}
				fi
			fi
		else
			echo -e "UART already configured in config.txt - \033[31mskipping\033[m"
		fi
	fi
}


# ---------------------------------

uname -a | grep -i osmc > /dev/null
if [ $? -eq 0 ]; then
	OSMC="1"
	HOMEDIR="/home/osmc"
	CONFIGDIR="/boot"
	FLAGS="-c22 -v4"
else
	# OpenELEC
	OSMC="0"
	HOMEDIR="/storage"
	CONFIGDIR="/flash"
	FLAGS="-c22 -v4"
fi

cd ${HOMEDIR}
if [ $? -ne 0 ]; then
	exit 2
fi
# install_autostart
# install_pibus
install_skin
install_dac_overlay
install_pi3_overlay

echo -e ""
if [ "$OSMC" -eq "1" ]; then
	echo -e "If you want to edit the autostart flags: \033[1;34msudo crontab -e\033[m"
else
	echo -e "If you want to edit the autostart flags: \033[1;34mnano ${HOMEDIR}/.config/autostart.sh\033[m"
fi
echo -e ""
echo -e "To see a list of possible flags        : \033[1;34m${HOMEDIR}/pibus -h\033[m"
echo -e ""
echo -e "\033[1;42mdone\033[m. Now type \033[31mreboot\033[m and install the skin via: Add-ons > My add-ons > .. > Install from zip file"


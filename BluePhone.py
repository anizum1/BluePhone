#!/usr/bin/env python3
"""
Ethical Device Remote Access Tool - Android & iOS
For accessing YOUR OWN devices with proper authorization
Requires: Python 3.8+, ADB (Android), libimobiledevice (iOS)
"""

import subprocess
import os
import sys
import time
import socket
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class AndroidAccess:
    def __init__(self):
        self.adb_path = self.check_adb()
        
    def check_adb(self):
        """Check if ADB is installed"""
        try:
            result = subprocess.run(['which', 'adb'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"{Colors.FAIL}ADB not found. Installing...{Colors.ENDC}")
                self.install_adb()
                return 'adb'
        except Exception as e:
            print(f"{Colors.FAIL}Error checking ADB: {e}{Colors.ENDC}")
            return None
    
    def install_adb(self):
        """Install ADB on Kali Linux"""
        print(f"{Colors.OKCYAN}Installing Android Debug Bridge (ADB)...{Colors.ENDC}")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'adb'], check=True)
            print(f"{Colors.OKGREEN}ADB installed successfully!{Colors.ENDC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Failed to install ADB: {e}{Colors.ENDC}")
            sys.exit(1)
    
    def check_scrcpy(self):
        """Check and install scrcpy if needed"""
        try:
            result = subprocess.run(['which', 'scrcpy'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"{Colors.WARNING}scrcpy not found. Installing...{Colors.ENDC}")
                self.install_scrcpy()
            return True
        except Exception as e:
            print(f"{Colors.FAIL}Error checking scrcpy: {e}{Colors.ENDC}")
            return False
    
    def install_scrcpy(self):
        """Install scrcpy on Kali Linux"""
        print(f"{Colors.OKCYAN}Installing scrcpy...{Colors.ENDC}")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'scrcpy'], check=True)
            print(f"{Colors.OKGREEN}scrcpy installed successfully!{Colors.ENDC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Failed to install scrcpy: {e}{Colors.ENDC}")
    
    def list_devices(self):
        """List connected Android devices"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            print(f"\n{Colors.OKBLUE}Connected Android Devices:{Colors.ENDC}")
            print(result.stdout)
            return result.stdout
        except Exception as e:
            print(f"{Colors.FAIL}Error listing devices: {e}{Colors.ENDC}")
            return None
    
    def connect_wireless(self, ip_address, port=5555):
        """Connect to Android device over WiFi"""
        print(f"{Colors.OKCYAN}Connecting to {ip_address}:{port}...{Colors.ENDC}")
        try:
            print(f"{Colors.WARNING}Note: Device must be connected via USB first to enable wireless debugging{Colors.ENDC}")
            subprocess.run(['adb', 'tcpip', str(port)], check=True)
            time.sleep(2)
            
            result = subprocess.run(['adb', 'connect', f'{ip_address}:{port}'], 
                                  capture_output=True, text=True)
            print(result.stdout)
            
            if 'connected' in result.stdout.lower():
                print(f"{Colors.OKGREEN}Successfully connected!{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.FAIL}Connection failed{Colors.ENDC}")
                return False
        except Exception as e:
            print(f"{Colors.FAIL}Error connecting wirelessly: {e}{Colors.ENDC}")
            return False
    
    def screen_mirror(self):
        """Mirror Android screen using scrcpy"""
        if not self.check_scrcpy():
            return
        
        print(f"\n{Colors.OKGREEN}Starting screen mirror...{Colors.ENDC}")
        print(f"{Colors.WARNING}Make sure USB debugging is enabled on your device{Colors.ENDC}")
        try:
            subprocess.run(['scrcpy'])
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}Screen mirror stopped{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error during screen mirror: {e}{Colors.ENDC}")
    
    def screen_record(self, output_file='android_record.mp4'):
        """Record Android screen"""
        print(f"\n{Colors.OKGREEN}Recording screen...{Colors.ENDC}")
        print(f"{Colors.WARNING}Press Ctrl+C to stop recording{Colors.ENDC}")
        try:
            subprocess.run(['scrcpy', '--record', output_file])
            print(f"{Colors.OKGREEN}Recording saved to {output_file}{Colors.ENDC}")
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}Recording stopped{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error during recording: {e}{Colors.ENDC}")
    
    def screenshot(self, output_file='android_screenshot.png'):
        """Take a screenshot of Android device"""
        print(f"\n{Colors.OKGREEN}Taking screenshot...{Colors.ENDC}")
        try:
            subprocess.run(['adb', 'shell', 'screencap', '-p', '/sdcard/screenshot.png'], check=True)
            subprocess.run(['adb', 'pull', '/sdcard/screenshot.png', output_file], check=True)
            subprocess.run(['adb', 'shell', 'rm', '/sdcard/screenshot.png'], check=True)
            print(f"{Colors.OKGREEN}Screenshot saved to {output_file}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error taking screenshot: {e}{Colors.ENDC}")
    
    def device_info(self):
        """Get device information"""
        print(f"\n{Colors.OKBLUE}Android Device Information:{Colors.ENDC}")
        try:
            model = subprocess.run(['adb', 'shell', 'getprop', 'ro.product.model'], 
                                 capture_output=True, text=True)
            print(f"Model: {model.stdout.strip()}")
            
            version = subprocess.run(['adb', 'shell', 'getprop', 'ro.build.version.release'], 
                                   capture_output=True, text=True)
            print(f"Android Version: {version.stdout.strip()}")
            
            battery = subprocess.run(['adb', 'shell', 'dumpsys', 'battery', '|', 'grep', 'level'], 
                                   capture_output=True, text=True, shell=True)
            print(f"Battery: {battery.stdout.strip()}")
            
            resolution = subprocess.run(['adb', 'shell', 'wm', 'size'], 
                                      capture_output=True, text=True)
            print(f"Screen: {resolution.stdout.strip()}")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error getting device info: {e}{Colors.ENDC}")

class iOSAccess:
    def __init__(self):
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check and install iOS tools"""
        tools = ['idevice_id', 'ideviceinfo', 'idevicescreenshot']
        missing = []
        
        for tool in tools:
            result = subprocess.run(['which', tool], capture_output=True, text=True)
            if result.returncode != 0:
                missing.append(tool)
        
        if missing:
            print(f"{Colors.WARNING}Missing iOS tools. Installing libimobiledevice...{Colors.ENDC}")
            self.install_dependencies()
    
    def install_dependencies(self):
        """Install libimobiledevice and related tools"""
        print(f"{Colors.OKCYAN}Installing iOS tools (libimobiledevice)...{Colors.ENDC}")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                          'libimobiledevice-utils', 'libimobiledevice6',
                          'usbmuxd', 'libusbmuxd-tools', 'ifuse'], check=True)
            
            # Install additional tools for screen mirroring
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                          'gstreamer1.0-tools', 'gstreamer1.0-plugins-base',
                          'gstreamer1.0-plugins-good', 'gstreamer1.0-plugins-bad'], check=True)
            
            print(f"{Colors.OKGREEN}iOS tools installed successfully!{Colors.ENDC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Failed to install iOS tools: {e}{Colors.ENDC}")
    
    def check_uxplay(self):
        """Check and guide installation of UxPlay for screen mirroring"""
        result = subprocess.run(['which', 'uxplay'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{Colors.WARNING}UxPlay not found.{Colors.ENDC}")
            return False
        return True
    
    def install_uxplay_guide(self):
        """Guide for installing UxPlay"""
        print(f"\n{Colors.OKBLUE}=== UxPlay Installation Guide ==={Colors.ENDC}")
        print(f"""
{Colors.OKCYAN}UxPlay enables AirPlay screen mirroring from iOS to Linux{Colors.ENDC}

Installation steps:

1. Install dependencies:
   sudo apt-get install cmake pkg-config
   sudo apt-get install libavahi-compat-libdnssd-dev libplist-dev
   sudo apt-get install libssl-dev libgstreamer1.0-dev
   sudo apt-get install libgstreamer-plugins-base1.0-dev

2. Clone and build UxPlay:
   cd ~
   git clone https://github.com/FDH2/UxPlay
   cd UxPlay
   mkdir build
   cd build
   cmake ..
   make
   sudo make install

3. After installation, return to this tool and use the iOS screen mirror option.

{Colors.WARNING}Alternative: Use QuickTime Player on macOS for official screen mirroring{Colors.ENDC}
        """)
    
    def list_devices(self):
        """List connected iOS devices"""
        try:
            result = subprocess.run(['idevice_id', '-l'], capture_output=True, text=True)
            print(f"\n{Colors.OKBLUE}Connected iOS Devices:{Colors.ENDC}")
            if result.stdout.strip():
                print(result.stdout)
                return result.stdout
            else:
                print(f"{Colors.WARNING}No iOS devices found{Colors.ENDC}")
                print(f"{Colors.OKCYAN}Make sure device is connected and you've tapped 'Trust' on the device{Colors.ENDC}")
                return None
        except Exception as e:
            print(f"{Colors.FAIL}Error listing iOS devices: {e}{Colors.ENDC}")
            return None
    
    def device_info(self, udid=None):
        """Get iOS device information"""
        print(f"\n{Colors.OKBLUE}iOS Device Information:{Colors.ENDC}")
        try:
            cmd = ['ideviceinfo']
            if udid:
                cmd.extend(['-u', udid])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                important_fields = ['DeviceName', 'ProductType', 'ProductVersion', 
                                  'ModelNumber', 'SerialNumber', 'WiFiAddress',
                                  'BluetoothAddress', 'BatteryCurrentCapacity']
                
                for line in lines:
                    for field in important_fields:
                        if field in line:
                            print(line)
            else:
                print(f"{Colors.FAIL}Error getting device info. Make sure device is trusted.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error getting iOS device info: {e}{Colors.ENDC}")
    
    def screenshot(self, output_file='ios_screenshot.png', udid=None):
        """Take a screenshot of iOS device"""
        print(f"\n{Colors.OKGREEN}Taking iOS screenshot...{Colors.ENDC}")
        try:
            cmd = ['idevicescreenshot']
            if udid:
                cmd.extend(['-u', udid])
            cmd.append(output_file)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}Screenshot saved to {output_file}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}Failed to take screenshot. Error: {result.stderr}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error taking screenshot: {e}{Colors.ENDC}")
    
    def screen_mirror_airplay(self):
        """Mirror iOS screen using AirPlay (UxPlay)"""
        if not self.check_uxplay():
            print(f"{Colors.WARNING}UxPlay is required for iOS screen mirroring{Colors.ENDC}")
            response = input(f"{Colors.OKCYAN}Show installation guide? (y/n): {Colors.ENDC}")
            if response.lower() == 'y':
                self.install_uxplay_guide()
            return
        
        print(f"\n{Colors.OKGREEN}Starting AirPlay receiver...{Colors.ENDC}")
        print(f"""{Colors.OKCYAN}
Instructions:
1. Make sure your iOS device and Linux machine are on the same WiFi network
2. On your iOS device, swipe down from top-right (or up from bottom)
3. Tap 'Screen Mirroring'
4. Select 'UxPlay' from the list
5. Your screen should appear on the Linux machine

Press Ctrl+C to stop screen mirroring
{Colors.ENDC}""")
        
        try:
            subprocess.run(['uxplay', '-n', 'UxPlay'])
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}Screen mirror stopped{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error during screen mirror: {e}{Colors.ENDC}")
    
    def mount_device(self, mount_point='/tmp/iphone'):
        """Mount iOS device filesystem"""
        print(f"\n{Colors.OKGREEN}Mounting iOS device...{Colors.ENDC}")
        try:
            os.makedirs(mount_point, exist_ok=True)
            
            result = subprocess.run(['ifuse', mount_point], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}Device mounted at {mount_point}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}You can now access files at {mount_point}{Colors.ENDC}")
                print(f"{Colors.WARNING}To unmount: fusermount -u {mount_point}{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}Failed to mount device{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error mounting device: {e}{Colors.ENDC}")
    
    def backup_device(self, backup_path='./ios_backup'):
        """Create iOS device backup"""
        print(f"\n{Colors.OKGREEN}Creating iOS backup...{Colors.ENDC}")
        print(f"{Colors.WARNING}This may take several minutes depending on device size{Colors.ENDC}")
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            cmd = ['idevicebackup2', 'backup', backup_path]
            subprocess.run(cmd, check=True)
            
            print(f"{Colors.OKGREEN}Backup completed successfully at {backup_path}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error creating backup: {e}{Colors.ENDC}")
    
    def pair_device(self):
        """Pair with iOS device"""
        print(f"\n{Colors.OKGREEN}Pairing with iOS device...{Colors.ENDC}")
        print(f"{Colors.WARNING}Make sure to tap 'Trust' on your device when prompted{Colors.ENDC}")
        try:
            subprocess.run(['idevicepair', 'pair'], check=True)
            print(f"{Colors.OKGREEN}Pairing successful!{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Pairing failed: {e}{Colors.ENDC}")

def print_banner():
    banner = f"""
{Colors.HEADER}
╔═══════════════════════════════════════════════════════════╗
║   Ethical Device Remote Access Tool                       ║
║   Android & iOS Support                                   ║
║   For authorized access to YOUR OWN devices only          ║
╚═══════════════════════════════════════════════════════════╝
{Colors.ENDC}
{Colors.WARNING}WARNING: This tool is for ethical use only!
- Only use on devices you own or have explicit permission to access
- Unauthorized access to devices is illegal
- Android: USB Debugging must be enabled
- iOS: Device must be trusted (tap 'Trust' when prompted){Colors.ENDC}
"""
    print(banner)

def print_main_menu():
    menu = f"""
{Colors.OKBLUE}╔═══════════════════════════════════════╗
║           MAIN MENU                   ║
╚═══════════════════════════════════════╝{Colors.ENDC}

{Colors.OKGREEN}[1]{Colors.ENDC}  Android Device Management
{Colors.OKGREEN}[2]{Colors.ENDC}  iOS Device Management
{Colors.OKGREEN}[0]{Colors.ENDC}  Exit

"""
    print(menu)

def print_android_menu():
    menu = f"""
{Colors.OKBLUE}╔═══════════════════════════════════════╗
║        ANDROID MANAGEMENT             ║
╚═══════════════════════════════════════╝{Colors.ENDC}

{Colors.OKGREEN}[1]{Colors.ENDC}  List Connected Devices
{Colors.OKGREEN}[2]{Colors.ENDC}  Mirror Device Screen (scrcpy)
{Colors.OKGREEN}[3]{Colors.ENDC}  Take Screenshot
{Colors.OKGREEN}[4]{Colors.ENDC}  Record Screen
{Colors.OKGREEN}[5]{Colors.ENDC}  Get Device Information
{Colors.OKGREEN}[6]{Colors.ENDC}  Connect Wirelessly (WiFi)
{Colors.OKGREEN}[0]{Colors.ENDC}  Back to Main Menu

"""
    print(menu)

def print_ios_menu():
    menu = f"""
{Colors.OKBLUE}╔═══════════════════════════════════════╗
║          iOS MANAGEMENT               ║
╚═══════════════════════════════════════╝{Colors.ENDC}

{Colors.OKGREEN}[1]{Colors.ENDC}  List Connected Devices
{Colors.OKGREEN}[2]{Colors.ENDC}  Pair Device
{Colors.OKGREEN}[3]{Colors.ENDC}  Get Device Information
{Colors.OKGREEN}[4]{Colors.ENDC}  Take Screenshot
{Colors.OKGREEN}[5]{Colors.ENDC}  Screen Mirror (AirPlay)
{Colors.OKGREEN}[6]{Colors.ENDC}  Mount Device Filesystem
{Colors.OKGREEN}[7]{Colors.ENDC}  Create Device Backup
{Colors.OKGREEN}[8]{Colors.ENDC}  UxPlay Installation Guide
{Colors.OKGREEN}[0]{Colors.ENDC}  Back to Main Menu

"""
    print(menu)

def android_menu(android):
    while True:
        print_android_menu()
        choice = input(f"{Colors.OKCYAN}Select an option: {Colors.ENDC}")
        
        if choice == '1':
            android.list_devices()
        elif choice == '2':
            android.screen_mirror()
        elif choice == '3':
            filename = input(f"{Colors.OKCYAN}Output filename (default: android_screenshot.png): {Colors.ENDC}") or 'android_screenshot.png'
            android.screenshot(filename)
        elif choice == '4':
            filename = input(f"{Colors.OKCYAN}Output filename (default: android_record.mp4): {Colors.ENDC}") or 'android_record.mp4'
            android.screen_record(filename)
        elif choice == '5':
            android.device_info()
        elif choice == '6':
            ip = input(f"{Colors.OKCYAN}Enter device IP address: {Colors.ENDC}")
            port = input(f"{Colors.OKCYAN}Enter port (default: 5555): {Colors.ENDC}") or '5555'
            android.connect_wireless(ip, int(port))
        elif choice == '0':
            break
        else:
            print(f"{Colors.FAIL}Invalid option. Please try again.{Colors.ENDC}")
        
        input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")
        os.system('clear')
        print_banner()

def ios_menu(ios):
    while True:
        print_ios_menu()
        choice = input(f"{Colors.OKCYAN}Select an option: {Colors.ENDC}")
        
        if choice == '1':
            ios.list_devices()
        elif choice == '2':
            ios.pair_device()
        elif choice == '3':
            ios.device_info()
        elif choice == '4':
            filename = input(f"{Colors.OKCYAN}Output filename (default: ios_screenshot.png): {Colors.ENDC}") or 'ios_screenshot.png'
            ios.screenshot(filename)
        elif choice == '5':
            ios.screen_mirror_airplay()
        elif choice == '6':
            mount_point = input(f"{Colors.OKCYAN}Mount point (default: /tmp/iphone): {Colors.ENDC}") or '/tmp/iphone'
            ios.mount_device(mount_point)
        elif choice == '7':
            backup_path = input(f"{Colors.OKCYAN}Backup path (default: ./ios_backup): {Colors.ENDC}") or './ios_backup'
            ios.backup_device(backup_path)
        elif choice == '8':
            ios.install_uxplay_guide()
        elif choice == '0':
            break
        else:
            print(f"{Colors.FAIL}Invalid option. Please try again.{Colors.ENDC}")
        
        input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")
        os.system('clear')
        print_banner()

def main():
    print_banner()
    
    android = AndroidAccess()
    ios = iOSAccess()
    
    while True:
        print_main_menu()
        choice = input(f"{Colors.OKCYAN}Select an option: {Colors.ENDC}")
        
        if choice == '1':
            os.system('clear')
            print_banner()
            android_menu(android)
        elif choice == '2':
            os.system('clear')
            print_banner()
            ios_menu(ios)
        elif choice == '0':
            print(f"\n{Colors.OKGREEN}Thank you for using Ethical Device Remote Access Tool!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"{Colors.FAIL}Invalid option. Please try again.{Colors.ENDC}")
        
        os.system('clear')
        print_banner()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.OKCYAN}Exiting...{Colors.ENDC}")
        sys.exit(0)

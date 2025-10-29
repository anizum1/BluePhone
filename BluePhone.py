#!/usr/bin/env python3
"""
Ethical Device Remote Access Tool - Android & iOS
For accessing YOUR OWN devices with proper authorization
Requires: Python 3.8+, ADB (Android), libimobiledevice (iOS)
Auto-installs all required dependencies
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

def run_command(cmd, check=False, capture=True, shell=False):
    """Helper function to run commands with better error handling"""
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check, shell=shell)
            return result
        else:
            result = subprocess.run(cmd, check=check, shell=shell)
            return result
    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}{Colors.ENDC}")
        if capture and e.stderr:
            print(f"{Colors.FAIL}Error: {e.stderr}{Colors.ENDC}")
        return None
    except Exception as e:
        print(f"{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        return None

class AndroidAccess:
    def __init__(self):
        self.adb_path = self.check_and_install_adb()
        
    def check_and_install_adb(self):
        """Check if ADB is installed, install if not"""
        result = run_command(['which', 'adb'])
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ ADB already installed{Colors.ENDC}")
            return result.stdout.strip()
        else:
            print(f"{Colors.WARNING}ADB not found. Installing...{Colors.ENDC}")
            return self.install_adb()
    
    def install_adb(self):
        """Install ADB on Kali Linux"""
        print(f"{Colors.OKCYAN}Installing Android Debug Bridge (ADB)...{Colors.ENDC}")
        
        # Update package list
        print("Updating package list...")
        run_command(['sudo', 'apt-get', 'update', '-y'])
        
        # Install ADB
        print("Installing ADB...")
        result = run_command(['sudo', 'apt-get', 'install', '-y', 'adb'])
        
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ ADB installed successfully!{Colors.ENDC}")
            return 'adb'
        else:
            print(f"{Colors.FAIL}✗ Failed to install ADB{Colors.ENDC}")
            return None
    
    def check_and_install_scrcpy(self):
        """Check and install scrcpy if needed"""
        result = run_command(['which', 'scrcpy'])
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ scrcpy already installed{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.WARNING}scrcpy not found. Installing...{Colors.ENDC}")
            return self.install_scrcpy()
    
    def install_scrcpy(self):
        """Install scrcpy on Kali Linux"""
        print(f"{Colors.OKCYAN}Installing scrcpy...{Colors.ENDC}")
        
        # Update package list
        run_command(['sudo', 'apt-get', 'update', '-y'])
        
        # Install scrcpy
        result = run_command(['sudo', 'apt-get', 'install', '-y', 'scrcpy'])
        
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ scrcpy installed successfully!{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ Failed to install scrcpy{Colors.ENDC}")
            return False
    
    def list_devices(self):
        """List connected Android devices"""
        result = run_command(['adb', 'devices'])
        if result:
            print(f"\n{Colors.OKBLUE}Connected Android Devices:{Colors.ENDC}")
            print(result.stdout)
            return result.stdout
        return None
    
    def connect_wireless(self, ip_address, port=5555):
        """Connect to Android device over WiFi"""
        print(f"{Colors.OKCYAN}Connecting to {ip_address}:{port}...{Colors.ENDC}")
        print(f"{Colors.WARNING}Note: Device must be connected via USB first to enable wireless debugging{Colors.ENDC}")
        
        run_command(['adb', 'tcpip', str(port)])
        time.sleep(2)
        
        result = run_command(['adb', 'connect', f'{ip_address}:{port}'])
        
        if result and 'connected' in result.stdout.lower():
            print(f"{Colors.OKGREEN}✓ Successfully connected!{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ Connection failed{Colors.ENDC}")
            return False
    
    def screen_mirror(self):
        """Mirror Android screen using scrcpy"""
        if not self.check_and_install_scrcpy():
            return
        
        print(f"\n{Colors.OKGREEN}Starting screen mirror...{Colors.ENDC}")
        print(f"{Colors.WARNING}Make sure USB debugging is enabled on your device{Colors.ENDC}")
        try:
            run_command(['scrcpy'], capture=False)
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}Screen mirror stopped{Colors.ENDC}")
    
    def screen_record(self, output_file='android_record.mp4'):
        """Record Android screen"""
        if not self.check_and_install_scrcpy():
            return
            
        print(f"\n{Colors.OKGREEN}Recording screen...{Colors.ENDC}")
        print(f"{Colors.WARNING}Press Ctrl+C to stop recording{Colors.ENDC}")
        try:
            run_command(['scrcpy', '--record', output_file], capture=False)
            print(f"{Colors.OKGREEN}Recording saved to {output_file}{Colors.ENDC}")
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}Recording stopped{Colors.ENDC}")
    
    def screenshot(self, output_file='android_screenshot.png'):
        """Take a screenshot of Android device"""
        print(f"\n{Colors.OKGREEN}Taking screenshot...{Colors.ENDC}")
        
        if run_command(['adb', 'shell', 'screencap', '-p', '/sdcard/screenshot.png'], check=True):
            if run_command(['adb', 'pull', '/sdcard/screenshot.png', output_file], check=True):
                run_command(['adb', 'shell', 'rm', '/sdcard/screenshot.png'])
                print(f"{Colors.OKGREEN}✓ Screenshot saved to {output_file}{Colors.ENDC}")
    
    def device_info(self):
        """Get device information"""
        print(f"\n{Colors.OKBLUE}Android Device Information:{Colors.ENDC}")
        
        model = run_command(['adb', 'shell', 'getprop', 'ro.product.model'])
        if model:
            print(f"Model: {model.stdout.strip()}")
        
        version = run_command(['adb', 'shell', 'getprop', 'ro.build.version.release'])
        if version:
            print(f"Android Version: {version.stdout.strip()}")
        
        battery = run_command(['adb', 'shell', 'dumpsys', 'battery'], shell=True)
        if battery:
            for line in battery.stdout.split('\n'):
                if 'level' in line:
                    print(f"Battery: {line.strip()}")
                    break
        
        resolution = run_command(['adb', 'shell', 'wm', 'size'])
        if resolution:
            print(f"Screen: {resolution.stdout.strip()}")

class iOSAccess:
    def __init__(self):
        self.check_and_install_dependencies()
        self.setup_usbmuxd()
    
    def check_and_install_dependencies(self):
        """Check and install iOS tools automatically"""
        tools = {
            'idevice_id': 'libimobiledevice-utils',
            'ideviceinfo': 'libimobiledevice-utils',
            'idevicescreenshot': 'libimobiledevice-utils',
            'idevicepair': 'libimobiledevice-utils',
            'ifuse': 'ifuse',
            'idevicebackup2': 'libimobiledevice-utils'
        }
        
        missing = []
        for tool, package in tools.items():
            result = run_command(['which', tool])
            if not result or result.returncode != 0:
                if package not in missing:
                    missing.append(package)
        
        if missing:
            print(f"{Colors.WARNING}Missing iOS tools. Installing...{Colors.ENDC}")
            self.install_dependencies(missing)
        else:
            print(f"{Colors.OKGREEN}✓ All iOS tools already installed{Colors.ENDC}")
    
    def install_dependencies(self, packages=None):
        """Install libimobiledevice and related tools"""
        print(f"{Colors.OKCYAN}Installing iOS tools...{Colors.ENDC}")
        
        # Update package list
        print("Updating package list...")
        run_command(['sudo', 'apt-get', 'update', '-y'])
        
        # Add universe repository
        print("Adding universe repository...")
        run_command(['sudo', 'add-apt-repository', '-y', 'universe'])
        run_command(['sudo', 'apt-get', 'update', '-y'])
        
        # Install all iOS tools including Avahi
        packages_to_install = [
            'libimobiledevice-utils',
            'libimobiledevice6',
            'usbmuxd',
            'libusbmuxd-tools',
            'ifuse',
            'avahi-daemon',
            'avahi-utils',
            'gstreamer1.0-tools',
            'gstreamer1.0-plugins-base',
            'gstreamer1.0-plugins-good',
            'gstreamer1.0-plugins-bad'
        ]
        
        print(f"Installing packages: {', '.join(packages_to_install)}")
        result = run_command(['sudo', 'apt-get', 'install', '-y'] + packages_to_install)
        
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ iOS tools installed successfully!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Some packages may have failed to install{Colors.ENDC}")
    
    def setup_usbmuxd(self):
        """Setup and start usbmuxd service"""
        print(f"{Colors.OKCYAN}Setting up usbmuxd service...{Colors.ENDC}")
        
        # Restart usbmuxd
        run_command(['sudo', 'systemctl', 'restart', 'usbmuxd'])
        run_command(['sudo', 'systemctl', 'enable', 'usbmuxd'])
        
        # Check if running
        result = run_command(['systemctl', 'is-active', 'usbmuxd'])
        if result and 'active' in result.stdout:
            print(f"{Colors.OKGREEN}✓ usbmuxd service is running{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ usbmuxd may not be running properly{Colors.ENDC}")
        
        # Setup and start Avahi daemon for AirPlay discovery
        print(f"{Colors.OKCYAN}Setting up Avahi daemon (required for AirPlay)...{Colors.ENDC}")
        run_command(['sudo', 'systemctl', 'restart', 'avahi-daemon'])
        run_command(['sudo', 'systemctl', 'enable', 'avahi-daemon'])
        
        # Check if Avahi is running
        result = run_command(['systemctl', 'is-active', 'avahi-daemon'])
        if result and 'active' in result.stdout:
            print(f"{Colors.OKGREEN}✓ Avahi daemon is running{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Avahi daemon may not be running properly{Colors.ENDC}")
        
        # Configure firewall for AirPlay
        print(f"{Colors.OKCYAN}Configuring firewall for AirPlay...{Colors.ENDC}")
        self.configure_firewall()
        
        # Add user to plugdev group
        username = os.environ.get('USER')
        if username:
            print(f"Adding {username} to plugdev group...")
            run_command(['sudo', 'usermod', '-a', '-G', 'plugdev', username])
    
    def configure_firewall(self):
        """Configure firewall to allow AirPlay connections"""
        # Check if ufw is installed
        result = run_command(['which', 'ufw'])
        if not result or result.returncode != 0:
            print(f"{Colors.WARNING}UFW not installed, skipping firewall configuration{Colors.ENDC}")
            return
        
        # Check if ufw is active
        result = run_command(['sudo', 'ufw', 'status'])
        if result and 'inactive' in result.stdout.lower():
            print(f"{Colors.OKCYAN}Firewall is inactive, no configuration needed{Colors.ENDC}")
            return
        
        print(f"{Colors.OKCYAN}Opening AirPlay ports in firewall...{Colors.ENDC}")
        
        # Allow AirPlay ports
        ports = [
            ('7000:7100/tcp', 'AirPlay TCP'),
            ('7000:7100/udp', 'AirPlay UDP'),
            ('5353/udp', 'mDNS'),
            ('49152:65535/tcp', 'AirPlay streaming')
        ]
        
        for port, description in ports:
            result = run_command(['sudo', 'ufw', 'allow', port])
            if result and result.returncode == 0:
                print(f"{Colors.OKGREEN}✓ Opened {description} ({port}){Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ Failed to open {description} ({port}){Colors.ENDC}")
        
        # Reload firewall
        run_command(['sudo', 'ufw', 'reload'])
        print(f"{Colors.OKGREEN}✓ Firewall configured for AirPlay{Colors.ENDC}")
    
    def check_uxplay(self):
        """Check if UxPlay is installed"""
        result = run_command(['which', 'uxplay'])
        return result and result.returncode == 0
    
    def install_uxplay_guide(self):
        """Guide for installing UxPlay"""
        print(f"\n{Colors.OKBLUE}=== UxPlay Installation Guide ==={Colors.ENDC}")
        print(f"""
{Colors.OKCYAN}UxPlay enables AirPlay screen mirroring from iOS to Linux{Colors.ENDC}

{Colors.OKGREEN}Installing UxPlay automatically...{Colors.ENDC}
        """)
        
        self.install_uxplay_auto()
    
    def install_uxplay_auto(self):
        """Automatically install UxPlay"""
        print(f"{Colors.OKCYAN}Installing UxPlay dependencies...{Colors.ENDC}")
        
        # Install dependencies
        deps = [
            'cmake', 'pkg-config', 'libavahi-compat-libdnssd-dev',
            'libplist-dev', 'libssl-dev', 'libgstreamer1.0-dev',
            'libgstreamer-plugins-base1.0-dev', 'git'
        ]
        
        run_command(['sudo', 'apt-get', 'update', '-y'])
        result = run_command(['sudo', 'apt-get', 'install', '-y'] + deps)
        
        if not result or result.returncode != 0:
            print(f"{Colors.FAIL}✗ Failed to install dependencies{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKCYAN}Cloning and building UxPlay...{Colors.ENDC}")
        
        # Clone UxPlay
        uxplay_dir = os.path.expanduser('~/UxPlay')
        if os.path.exists(uxplay_dir):
            print(f"Removing old UxPlay directory...")
            run_command(['rm', '-rf', uxplay_dir])
        
        os.chdir(os.path.expanduser('~'))
        result = run_command(['git', 'clone', 'https://github.com/FDH2/UxPlay'])
        
        if not result or result.returncode != 0:
            print(f"{Colors.FAIL}✗ Failed to clone UxPlay{Colors.ENDC}")
            return False
        
        # Build UxPlay
        os.chdir(uxplay_dir)
        os.makedirs('build', exist_ok=True)
        os.chdir('build')
        
        print("Running cmake...")
        if not run_command(['cmake', '..']):
            print(f"{Colors.FAIL}✗ cmake failed{Colors.ENDC}")
            return False
        
        print("Running make...")
        if not run_command(['make']):
            print(f"{Colors.FAIL}✗ make failed{Colors.ENDC}")
            return False
        
        print("Installing UxPlay...")
        if not run_command(['sudo', 'make', 'install']):
            print(f"{Colors.FAIL}✗ Installation failed{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✓ UxPlay installed successfully!{Colors.ENDC}")
        
        # Return to original directory
        os.chdir(os.path.expanduser('~'))
        return True
    
    def list_devices(self):
        """List connected iOS devices"""
        result = run_command(['idevice_id', '-l'])
        
        print(f"\n{Colors.OKBLUE}Connected iOS Devices:{Colors.ENDC}")
        if result and result.stdout.strip():
            print(result.stdout)
            return result.stdout
        else:
            print(f"{Colors.WARNING}No iOS devices found{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Make sure:")
            print("  1. Device is connected via USB")
            print("  2. Device is unlocked")
            print(f"  3. You tapped 'Trust' on the device{Colors.ENDC}")
            return None
    
    def device_info(self, udid=None):
        """Get iOS device information"""
        print(f"\n{Colors.OKBLUE}iOS Device Information:{Colors.ENDC}")
        
        cmd = ['ideviceinfo']
        if udid:
            cmd.extend(['-u', udid])
        
        result = run_command(cmd)
        
        if result and result.returncode == 0:
            lines = result.stdout.split('\n')
            important_fields = ['DeviceName', 'ProductType', 'ProductVersion', 
                              'ModelNumber', 'SerialNumber', 'WiFiAddress',
                              'BluetoothAddress', 'BatteryCurrentCapacity']
            
            for line in lines:
                for field in important_fields:
                    if field in line:
                        print(line)
        else:
            print(f"{Colors.FAIL}✗ Error getting device info. Make sure device is trusted.{Colors.ENDC}")
    
    def screenshot(self, output_file='ios_screenshot.png', udid=None):
        """Take a screenshot of iOS device"""
        print(f"\n{Colors.OKGREEN}Taking iOS screenshot...{Colors.ENDC}")
        
        cmd = ['idevicescreenshot']
        if udid:
            cmd.extend(['-u', udid])
        cmd.append(output_file)
        
        result = run_command(cmd)
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ Screenshot saved to {output_file}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Failed to take screenshot{Colors.ENDC}")
            if result and result.stderr:
                print(f"{Colors.FAIL}Error: {result.stderr}{Colors.ENDC}")
    
    def screen_mirror_airplay(self):
        """Mirror iOS screen using AirPlay (UxPlay)"""
        if not self.check_uxplay():
            print(f"{Colors.WARNING}UxPlay is not installed{Colors.ENDC}")
            response = input(f"{Colors.OKCYAN}Install UxPlay now? (y/n): {Colors.ENDC}")
            if response.lower() == 'y':
                if not self.install_uxplay_auto():
                    return
            else:
                return
        
        # Check network interface
        print(f"\n{Colors.OKCYAN}Checking network configuration...{Colors.ENDC}")
        result = run_command(['ip', 'addr', 'show'])
        if result:
            print(f"{Colors.OKBLUE}Available network interfaces:{Colors.ENDC}")
            lines = result.stdout.split('\n')
            interfaces = []
            for line in lines:
                if 'wlan' in line or 'wlp' in line or 'eth' in line or 'enp' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        iface = parts[1].strip().split('@')[0]
                        if iface not in interfaces:
                            interfaces.append(iface)
                            print(f"  - {iface}")
        
        print(f"\n{Colors.OKGREEN}Starting AirPlay receiver...{Colors.ENDC}")
        print(f"""{Colors.OKCYAN}
Instructions:
1. Make sure your iOS device and Linux machine are on the SAME WiFi network
2. On your iOS device, swipe down from top-right (or up from bottom)
3. Tap 'Screen Mirroring'
4. Wait 10-15 seconds for 'UxPlay' to appear in the list
5. Tap 'UxPlay' to connect
6. Your screen should appear on the Linux machine

Troubleshooting:
- If 'UxPlay' doesn't appear, make sure both devices are on the same WiFi
- Try restarting UxPlay (Ctrl+C and run again)
- Check that Avahi daemon is running: systemctl status avahi-daemon

Press Ctrl+C to stop screen mirroring
{Colors.ENDC}""")
        
        # Check if Avahi is running
        result = run_command(['systemctl', 'is-active', 'avahi-daemon'])
        if not result or 'active' not in result.stdout:
            print(f"{Colors.WARNING}⚠ Avahi daemon is not running. Starting it now...{Colors.ENDC}")
            run_command(['sudo', 'systemctl', 'start', 'avahi-daemon'])
            time.sleep(2)
        
        try:
            # Run UxPlay with better compatibility options
            print(f"{Colors.OKGREEN}Starting UxPlay...{Colors.ENDC}")
            run_command(['uxplay', '-n', 'UxPlay', '-v'], capture=False)
        except KeyboardInterrupt:
            print(f"\n{Colors.OKCYAN}Screen mirror stopped{Colors.ENDC}")
    
    def mount_device(self, mount_point='/tmp/iphone'):
        """Mount iOS device filesystem"""
        print(f"\n{Colors.OKGREEN}Mounting iOS device...{Colors.ENDC}")
        
        os.makedirs(mount_point, exist_ok=True)
        
        result = run_command(['ifuse', mount_point])
        
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ Device mounted at {mount_point}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}You can now access files at {mount_point}{Colors.ENDC}")
            print(f"{Colors.WARNING}To unmount: fusermount -u {mount_point}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Failed to mount device{Colors.ENDC}")
    
    def backup_device(self, backup_path='./ios_backup'):
        """Create iOS device backup"""
        print(f"\n{Colors.OKGREEN}Creating iOS backup...{Colors.ENDC}")
        print(f"{Colors.WARNING}This may take several minutes depending on device size{Colors.ENDC}")
        
        os.makedirs(backup_path, exist_ok=True)
        
        cmd = ['idevicebackup2', 'backup', backup_path]
        result = run_command(cmd, capture=False)
        
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ Backup completed successfully at {backup_path}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Backup failed{Colors.ENDC}")
    
    def pair_device(self):
        """Pair with iOS device"""
        print(f"\n{Colors.OKGREEN}Pairing with iOS device...{Colors.ENDC}")
        print(f"{Colors.WARNING}Make sure to tap 'Trust' on your device when prompted{Colors.ENDC}")
        
        # First, unpair to reset
        run_command(['idevicepair', 'unpair'])
        
        # Pair
        result = run_command(['idevicepair', 'pair'])
        
        if result and result.returncode == 0:
            print(f"{Colors.OKGREEN}✓ Pairing successful!{Colors.ENDC}")
            
            # Validate
            time.sleep(1)
            validate = run_command(['idevicepair', 'validate'])
            if validate and 'SUCCESS' in validate.stdout:
                print(f"{Colors.OKGREEN}✓ Pairing validated!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Pairing failed. Make sure you tapped 'Trust' on your device{Colors.ENDC}")
    
    def network_diagnostics(self):
        """Run network diagnostics for AirPlay troubleshooting"""
        print(f"\n{Colors.OKBLUE}=== Network Diagnostics for AirPlay ==={Colors.ENDC}\n")
        
        # Check network interfaces
        print(f"{Colors.OKCYAN}1. Network Interfaces:{Colors.ENDC}")
        result = run_command(['ip', 'addr', 'show'])
        if result:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'inet ' in line and '127.0.0.1' not in line:
                    print(f"   {line.strip()}")
        
        # Check Avahi status
        print(f"\n{Colors.OKCYAN}2. Avahi Daemon Status:{Colors.ENDC}")
        result = run_command(['systemctl', 'is-active', 'avahi-daemon'])
        if result and 'active' in result.stdout:
            print(f"   {Colors.OKGREEN}✓ Avahi is running{Colors.ENDC}")
        else:
            print(f"   {Colors.FAIL}✗ Avahi is NOT running{Colors.ENDC}")
            response = input(f"\n{Colors.OKCYAN}Start Avahi daemon? (y/n): {Colors.ENDC}")
            if response.lower() == 'y':
                run_command(['sudo', 'systemctl', 'start', 'avahi-daemon'])
                print(f"   {Colors.OKGREEN}✓ Avahi started{Colors.ENDC}")
        
        # Check for AirPlay services
        print(f"\n{Colors.OKCYAN}3. Scanning for AirPlay devices on network...{Colors.ENDC}")
        result = run_command(['avahi-browse', '-a', '-t', '-r'], capture=True)
        if result:
            if '_airplay' in result.stdout.lower() or '_raop' in result.stdout.lower():
                print(f"   {Colors.OKGREEN}✓ AirPlay services detected on network{Colors.ENDC}")
            else:
                print(f"   {Colors.WARNING}⚠ No AirPlay services detected{Colors.ENDC}")
        
        # Check firewall status
        print(f"\n{Colors.OKCYAN}4. Firewall Status:{Colors.ENDC}")
        result = run_command(['sudo', 'ufw', 'status'])
        if result:
            if 'inactive' in result.stdout.lower():
                print(f"   {Colors.OKGREEN}✓ Firewall is inactive (no blocking){Colors.ENDC}")
            else:
                print(f"   {Colors.WARNING}Firewall is active{Colors.ENDC}")
                if '7000' in result.stdout and '5353' in result.stdout:
                    print(f"   {Colors.OKGREEN}✓ AirPlay ports are open{Colors.ENDC}")
                else:
                    print(f"   {Colors.WARNING}⚠ AirPlay ports may be blocked{Colors.ENDC}")
                    response = input(f"\n{Colors.OKCYAN}Open AirPlay ports? (y/n): {Colors.ENDC}")
                    if response.lower() == 'y':
                        self.configure_firewall()
        
        # Check if UxPlay is installed
        print(f"\n{Colors.OKCYAN}5. UxPlay Status:{Colors.ENDC}")
        if self.check_uxplay():
            print(f"   {Colors.OKGREEN}✓ UxPlay is installed{Colors.ENDC}")
        else:
            print(f"   {Colors.FAIL}✗ UxPlay is NOT installed{Colors.ENDC}")
        
        # Recommendations
        print(f"\n{Colors.OKBLUE}=== Recommendations ==={Colors.ENDC}")
        print(f"""
{Colors.OKCYAN}For successful AirPlay mirroring:{Colors.ENDC}
1. Ensure iPhone and Linux are on the SAME WiFi network
2. Make sure Avahi daemon is running (checked above)
3. Ensure firewall allows AirPlay ports (checked above)
4. When starting UxPlay, wait 10-15 seconds before checking iPhone
5. On iPhone: Settings → WiFi → Verify network name matches Linux
6. Try restarting UxPlay if device doesn't appear
        """)

def print_banner():
    banner = f"""
{Colors.HEADER}
╔═══════════════════════════════════════════════════════════╗
║   Ethical Device Remote Access Tool v2.0                  ║
║   Android & iOS Support - Auto-Install Dependencies       ║
║   For authorized access to YOUR OWN devices only          ║
╚═══════════════════════════════════════════════════════════╝
{Colors.ENDC}
{Colors.WARNING}WARNING: This tool is for ethical use only!
- Only use on devices you own or have explicit permission to access
- Unauthorized access to devices is illegal
- All dependencies will be installed automatically{Colors.ENDC}
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
{Colors.OKGREEN}[8]{Colors.ENDC}  Network Diagnostics
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
            ios.network_diagnostics()
        elif choice == '0':
            break
        else:
            print(f"{Colors.FAIL}Invalid option. Please try again.{Colors.ENDC}")
        
        input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")
        os.system('clear')
        print_banner()

def main():
    print_banner()
    
    print(f"\n{Colors.OKCYAN}Initializing and checking dependencies...{Colors.ENDC}\n")
    
    # Initialize classes (will auto-install dependencies)
    android = AndroidAccess()
    ios = iOSAccess()
    
    print(f"\n{Colors.OKGREEN}✓ All dependencies checked and installed!{Colors.ENDC}")
    time.sleep(2)
    
    os.system('clear')
    print_banner()
    
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
        # Check if running with sufficient privileges
        if os.geteuid() == 0:
            print(f"{Colors.WARNING}Warning: Running as root is not recommended.{Colors.ENDC}")
            print(f"{Colors.WARNING}The script will use sudo when needed.{Colors.ENDC}")
            time.sleep(2)
        
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.OKCYAN}Exiting...{Colors.ENDC}")
        sys.exit(0)

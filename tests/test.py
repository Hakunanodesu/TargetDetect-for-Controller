import wmi

def get_cpu_info():
    w = wmi.WMI()
    for cpu in w.Win32_Processor():
        vendor = cpu.Manufacturer  # 厂商，如 "GenuineIntel" 或 "AuthenticAMD"
        name = cpu.Name            # 型号，如 "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz"
        return vendor, name

vendor, model = get_cpu_info()
print(f"CPU 厂商: {vendor}")
print(f"CPU 型号: {model}")

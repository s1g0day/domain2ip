# coding : utf-8
import dns.resolver
import sys
import ipwhois
import os
import csv
import threading
from telnetlib import Telnet
from pycountry import countries
import time
import argparse
import requests
from bs4 import BeautifulSoup

try:    # Ugly hack because Python3 decided to rename Queue to queue
    import Queue
except ImportError:
    import queue as Queue
    
def logo():
    print("""
  _____ _             _        _____      _   
 / ____| |           | |      / ____|    | |  
| (___ | |_ _   _  __| |_   _| |     __ _| |_ 
 \___ \| __| | | |/ _` | | | | |    / _` | __|
 ____) | |_| |_| | (_| | |_| | |___| (_| | |_ 
|_____/ \__|\__,_|\__,_|\__, |\_____\__,_|\__|
                         __/ |                
                        |___/     
                         
            https://www.cnblogs.com/StudyCat/
    
    """)
    

class scanner(threading.Thread):
    def __init__(self, queue,ports):
        global domainInfo
        threading.Thread.__init__(self)
        self.queue = queue
        self.ports = ports    

    def get_ipinfo(self, domain):
            try:
                if sys.stdout.isatty():     # Don't spam output if redirected
                    sys.stdout.write(domain + "                              \r")
                    sys.stdout.flush()
                ipaddr = nslookup(domain)
                if not ipaddr:
                    pass
                    #print("None of DNS query names exist: %s"%(domain))
                else:
                    httpinfo = HTTPHeaders(domain)
                    if httpinfo:
                        title = httpinfo['title']
                        status_code = httpinfo['status_code']
                        httpserver = httpinfo['httpserver']
                    else:    
                        title = ""
                        status_code = ""
                        httpserver = ""                      
                    ipinfo = iplookup(ipaddr)
                    msg = ""
                    for port in self.ports:
                        if do_telnet(ipaddr,port):
                            msg = msg + port+"|"
                    if msg:
                        msg = msg[:-1]+"(open)" 
                    res = {'Hostname':domain,'IPAddr':ipaddr,'ISP':ipinfo['isp'],'Country':ipinfo['country'],'asn_cidr':ipinfo['asn_cidr'],'asn_description':ipinfo['asn_description'],'PortScan':msg,'StatusCode':status_code,'httpserver':httpserver,'Title':title} 
                    domainInfo.append(res)    
            except Exception as e:
                pass

    def run(self):
        while True:
            try:
                domain = self.queue.get(timeout=1)
            except Exception as e:
                return
            self.get_ipinfo(domain)
            self.queue.task_done()

def nslookup(domain):
    try:
        res = resolver.resolve(domain, "A")
        return res[0].address
    except Exception as e:
        return

def save2csv(data,filename):
    with open(filename, 'w', newline='',encoding='utf-8-sig') as csvfile:
        fieldnames = ['Hostname', 'IPAddr','Country','ISP','asn_cidr','asn_description','PortScan','StatusCode','httpserver','Title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i in range(len(data)):
            writer.writerow(data[i])

def HTTPHeaders(domain):
    url = 'http://'+domain.strip()
    url2 = 'https://'+domain.strip()
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36'}
    try:
        r = requests.get(url,headers=headers,allow_redirects=True,timeout=6)
    except Exception as e:
        try:
            r = requests.get(url2,headers=headers,allow_redirects=True,timeout=6)
        except Exception as e:
            return

    try:        
        if requests.utils.get_encodings_from_content(r.text):
            coding = requests.utils.get_encodings_from_content(r.text)[0]
        else:
            coding = 'utf-8'
        if r.encoding:
            html = r.text.encode(r.encoding,"ignore").decode(coding,"ignore")
        else:
            html = r.text
        soup = BeautifulSoup(html, "html.parser")
        if soup.title:
            title = soup.title.string
        else:
            title = ""
    except Exception as e:
        pass         
    
    status_code = str(r.status_code) + ' ' + requests.status_codes._codes[r.status_code][0]
    if 'server' in r.headers:
        httpserver = r.headers['server']
    else:
        httpserver = 'Unknown'
    
    return {'title':title,'status_code':status_code,'httpserver':httpserver} 

def iplookup(ipaddr):
    try:
        info = ipwhois.IPWhois(ipaddr).lookup_whois()
    except Exception as e:
        return {'country':'Unknown','isp':'Unknown','asn_cidr':'Private-Use Networks','asn_description':'Private-Use Networks'}
   # city = info['nets'][0]['city']?info['nets'][0]['city']:""   
    city = (info['nets'][0]['city']  if(info['nets'][0]['city']) else "")     
    country = countries.get(alpha_2=info['nets'][0]['country'])
    if city:
        countryname = country.name +'/'+city
    else:
        countryname = country.name
    if info['nets'][0]['description']:
        temp = info['nets'][0]['description'].splitlines()
        ipinfo = {'country':countryname,'isp':temp[0],'asn_cidr':info['asn_cidr'],'asn_description':info['asn_description']}
    else:
        ipinfo = {'country':countryname,'isp':'Not Found','asn_cidr':info['asn_cidr'],'asn_description':info['asn_description']}
    return ipinfo

def do_telnet(ip,port):
    server = Telnet()
    try:
        server.open(ip,port,timeout=4)
        return True
    except Exception as e:
        return False
    finally:
        server.close()
        
def get_args():
    global args
    
    parser = argparse.ArgumentParser('domain2ip.py', formatter_class=lambda prog:argparse.HelpFormatter(prog,max_help_position=40))
    parser.add_argument('-w', '--wordlist', help='Lines contain domain names, one per line', dest='wordlist', required=False,default="domains.txt")
    parser.add_argument('-p', '--port', help='Ports to scan', dest='ports', required=False,default="80,443")
    parser.add_argument('-t', '--threads', help='Number of threads', dest='threads', required=False, type=int, default=8)
    parser.add_argument('-o', '--output', help="Write output to a csv file", dest='output_filename', required=False,default="output.csv")
    parser.add_argument('-w3', '--www', action="store_true", default=False, help='Add www to domain', dest='w3', required=False)
    args = parser.parse_args()     

def main():
    starttime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print("Working......")
    global resolver,domainInfo
    queue = Queue.Queue()
    domainInfo = []
    domain_file = args.wordlist
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 3
    resolver.nameservers = ['119.29.29.29','114.114.114.114','8.8.8.8']
    
    if os.path.exists(domain_file):
        with open(domain_file,'r') as file:
            domain_list = file.read().splitlines()
            print("Adding domains to queue,total: %d" %(len(domain_list)))
            for domain in domain_list:
                if args.w3:
                    queue.put('www.'+domain)
                else:
                    queue.put(domain)
    else:
        print("%s not found!" %(domain_file))
        sys.exit(1)
    threads = args.threads
    threads_list = []
    ports = args.ports.split(',')
    try:
        for i in range(threads):
            t = scanner(queue,ports)
            t.setDaemon(True)
            threads_list.append(t)
        
        for i in range(threads):
            threads_list[i].start()
        
        for i in range(threads):
            threads_list[i].join(1024)        
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, quitting...")
        sys.exit(1)
    time.sleep(1)    
    try:        
        save2csv(domainInfo,args.output_filename)
    except Exception as e:
        print(e)
    print("The scan result has been saved to %s" % (args.output_filename))    
    print ("Start at %s \t End at %s" %(starttime,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))    

if __name__ == "__main__":
    logo()
    get_args()
    main()

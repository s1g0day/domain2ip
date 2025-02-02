
# domain2ip

批量解析子域名，获取IP地址、所在地、ISP、ASN网段、ASN描述信息、简单端口扫描、尝试获取HTTP状态码、httpserver及网页标题，并保存到csv文件方便进一步筛选目标。  

# 环境
~~~
os:windows 10
python:3.7.9
python模块：pip3 install -r requirements.txt
~~~
# 使用
~~~
domain2ip.py -h  
optional arguments:  
-h, --help                            show this help message and exit  
-w WORDLIST, --wordlist WORDLIST      Lines contain domain names, one per line  
-p PORTS, --port PORTS                Ports to scan  
-t THREADS, --threads THREADS         Number of threads  
-o OUTPUT_FILENAME, --output OUTPUT_FILENAME Write output to a csv file  
~~~

# 截图
 ![Image text](https://github.com/telllpu/domain2ip/blob/master/Capture.PNG)

# 使用案例
~~~
python domain2ip.py -f domains.txt -p 1-65535 -t 1000 -o data.csv
或
ps：脚本默认选择 domains.txt，可以不加-f 参数
python domain2ip.py -p 1-65535 -t 1000 -o data.csv
~~~
# 参考
感谢 @[StudyCat404(https://github.com/StudyCat404/domain2ip) 大佬提供的脚本

我在使用时发现一些模块的版本可能高于大佬的开发版本，所以就做了一些小的改动，顺便添加上了脚本的模块列表requirements.txt

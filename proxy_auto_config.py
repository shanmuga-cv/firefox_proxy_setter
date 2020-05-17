import jinja2
import os

pac_file_location = "proxy.pac"

_pac_template = """function FindProxyForURL(){return "PROXY {{ip}}:{{port}}";}"""


def set_proxy(proxy_ip, proxy_port):
    with open(pac_file_location, "w") as fout:
        pac_config = jinja2.Template(_pac_template).render(ip=proxy_ip, port=proxy_port)
        fout.write(pac_config)


def unset_proxy():
    os.remove(_pac_template)


if __name__ == "__main__":
    import sys

    ip, port_str = sys.argv[1:3]
    set_proxy(ip, int(port_str))

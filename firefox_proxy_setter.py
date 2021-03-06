import os, glob, jinja2, platform
import logging


logger = logging.getLogger("firefox_proxy_setter.setter")

def set_proxy(proxy_ip, proxy_port):
    with open("user.js.jinja2") as template_file:
        template = jinja2.Template(template_file.read())
    firefox_proxy_config_values = template.render(proxy_ip = proxy_ip, proxy_port = proxy_port)
    user_prefs_file = _get_user_pref_file()
    with open(user_prefs_file, 'w') as user_prefs_file:
        user_prefs_file.write(firefox_proxy_config_values)


def unset_proxy():
    os.remove(_get_user_pref_file())


def _get_user_pref_file():
    os_platform = platform.system()
    logger.debug("got os platform: %s", os_platform)
    if os_platform == "Windows":
        app_data_dir = os.getenv('APPDATA')
        firefox_profile_path = ['Mozilla', 'Firefox', 'Profiles', '*.default-release*']
        firefox_profile_pattern = os.path.join(*([app_data_dir] + firefox_profile_path))
    elif os_platform == "Darwin":
        home_dir = os.path.expanduser("~")
        firefox_profile_path = [home_dir, "Library", "Application Support", "Firefox", "Profiles", "*.default"]
        firefox_profile_pattern = os.path.join(*firefox_profile_path)
    logger.debug("firefox_profile_pattern: %s", firefox_profile_pattern)
    search_results = glob.glob(firefox_profile_pattern)
    assert len(search_results) == 1, f"no directory matched for pattern {firefox_profile_pattern}"
    firefox_profile_dir = search_results[0]
    assert os.path.isdir(firefox_profile_dir), f"not a directory {firefox_profile_dir}"
    return os.path.join(firefox_profile_dir, "user.js")


if __name__ ==  "__main__":
    import sys
    ip, port_str = sys.argv[1:3] 
    set_proxy(ip, int(port_str))
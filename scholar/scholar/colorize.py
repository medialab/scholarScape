class colorize:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    
    @classmethod
    def blue(self,string): return colorize.OKBLUE + str(string) + colorize.ENDC
    @classmethod
    def green(self,string): return colorize.OKGREEN + str(string) + colorize.ENDC
    @classmethod
    def red(self,string): return colorize.FAIL + str(string) + colorize.ENDC

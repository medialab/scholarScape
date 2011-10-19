class colorize:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''
    
    @classmethod
    def blue(self,string): print colorize.OKBLUE + str(string) + colorize.ENDC
    @classmethod
    def green(self,string): print colorize.OKGREEN + str(string) + colorize.ENDC
    @classmethod
    def red(self,string): print colorize.FAIL + str(string) + colorize.ENDC

import time, sys, re, getopt, random, threading,shutil
import xml.dom.minidom

import globals

class Configuration(object):
    def __init__(self):
        self.config={}
        self.options={}
        self.lock=threading.RLock()

    class Option:
        def __init__(self,short,long,text,default=None,hasparam=False):
            self.shortoption=short
            self.longoption=long
            self.text=text
            self.default=default
            self.hasparameter=hasparam

    def setOption(self,key,opt):
        if opt == None:
            if self.options.has_key(key):
                del self.options[key]
        else:
            self.options[key]=opt

    def printOptions(self):
        print "Options:"
        # some sorting might be preferred, but we just print the option
        # list as we get it
        for k in self.options.keys():
            format="%s %s%s%s"
            shortoption="   "
            longoption=""
            filler=""
            text=""
            if self.options[k].shortoption!=None:
                # has a short option
                shortoption=self.options[k].shortoption + " "
            if self.options[k].longoption!=None:
                longoption=self.options[k].longoption

            if len(longoption) > 15:
                filler=" "
            else:
                filler="%"+str(16 - len(longoption)) + "s"
                filler=filler%(" ")

            text=self.options[k].text
            print format%(shortoption,longoption,filler,text)
        print ""

    def readArguments(self,args,header,usage):
        try:
            opts,files=mygetopt(args,self.options)
        except getopt.GetoptError:
            # print help information and exit:
            header()
            print "Invalid option or argument "+ str(sys.exc_info()[1])
            usage()
            sys.exit(1)

        self.config["save-on-set"]=False
        for k in self.options.keys():
            if self.options[k].default!=None:
                self.setValue(k,self.options[k].default)

        # implement our own options: configuration, verbose, help, trace
        vopt=self.options["verbose"]
        hopt=self.options["help"]
        copt=self.options["configuration"]
        topt=self.options["trace"]
        for o in opts:
            if o[0] in (hopt.shortoption,hopt.longoption):
                header()
                usage()
                sys.exit()
            if o[0] in (copt.shortoption,copt.longoption):
                self.addValue("configuration",o[1])
            if o[0] in (vopt.shortoption,vopt.longoption):
                self.setValue('verbose',True)
            if o[0] in (topt.shortoption,topt.longoption):
                v=o[1].split(",")
                var={}
                for vv in v:
                    if len(vv)>0:
                        var[vv]=True
                self.setValue("trace",var)

        if self.getValue("verbose"):
            globals.Reporter.verbose=True
        if self.getValue("trace")!=None:
            globals.Reporter.trace=self.getValue("trace")
            globals.Reporter.message("trace set to " + str(globals.Reporter.trace.keys()))

        configfiles=self.getValue("configuration")
        index=0
        allowoverride=True
        globals.Reporter.message("reading "+ str(len(configfiles)) + " files")
        if configfiles != None and len(configfiles)>0:
            while index < len(configfiles):
                globals.Reporter.message("reading configuration file " + str(configfiles[index]))
                self.readConfig(configfiles[index],allowoverride)
                allowoverride=False # only the first file can overwrite settings
                # get the variable again, to allow configuration files being appended
                configfiles=self.getValue("configuration")
                index+=1

        # then reread the command line arguments and override whatever is set
        # in the configuration files
        for o in opts:
            for k in self.options.keys():
                if self.options[k].shortoption==o[0] or self.options[k].longoption==o[0]:
                    v=[True]
                    if self.options[k].hasparameter:
                        v=o[1].split(",")

                    var=self.getValue(k)
                    for vv in v:
                        if var==None:
                            var=vv
                        elif isinstance(var,dict):
                            var[vv]=True
                        elif isinstance(var,list):
                            var.append(vv)
                        elif isinstance(var,int):
                            try:
                                var=int(vv)
                            except:
                                var=0
                        elif isinstance(var,float):
                            try:
                                var=float(vv)
                            except:
                                var=0.0
                        else:
                            var=vv
                    globals.Reporter.message("setting config value "+str(k)+" to "+str(var),'control')
                    self.setValue(k,var)
                    break

        return files

    def readConfig(self,path,override=False):
        # open the config file at path and parse the contents
        doc=None
        try:
            globals.Reporter.message( "loading configuration " + path)
            doc=xml.dom.minidom.parse(path)
        except:
            # skip file not found errors
            globals.Reporter.message("caught exception on parsing config: " + str(sys.exc_info()[0]))

        if not doc == None:
            #for node in doc.childNodes:
            #    message("node " + str(node.localName))

            # look for a node named 'configuration'
            doc2=self.findRoot(doc)
            if doc2.hasChildNodes():
                for node in doc2.childNodes:
                    (key,val)=self.readNode(node,override)
                    if key != None and (override or (not self.config.has_key(key))):
                        #globals.Reporter.message("config[" + key + "]=" + str(val))
                        self.setValue(key,val)
            doc.unlink()

    def readNode(self,node,override):
        if node.nodeType == xml.dom.Node.ELEMENT_NODE and node.localName.lower() == "key":
            key=node.getAttribute('id')
            val=node.getAttribute('value')

            if val == None:
                val = False
            return (key,val)
        elif node.nodeType == xml.dom.Node.ELEMENT_NODE:
            key=node.localName
            tp=node.getAttribute("type")
            if tp==None or tp=="":
                tp="list"
            retval=[]
            if tp=="hash":
                retval={}
            if node.hasChildNodes():
                for node2 in node.childNodes:
                    (key2,val)=self.readNode(node2,override)
                    if tp=="list" and (not val==None):
                        retval.append(val)
                    elif tp=="hash" and not (key2==None or val==None):
                        retval[key2]=val
            return (key,retval)
        else:
            # non-element node (text, etc)
            return (None,None)

    def findRoot(self,doc):
        if doc.nodeType == xml.dom.Node.ELEMENT_NODE and doc.localName.lower() == "configuration":
            return doc
        elif doc.hasChildNodes():
            # breadth first, then depth
            for node in doc.childNodes:
                if node.nodeType == xml.dom.Node.ELEMENT_NODE and node.localName.lower() == "configuration":
                    return node
            for node in doc.childNodes:
                doc2=self.findRoot(node)
                if not doc2 == None:
                    return doc2
        return None

    def writeConfig(self,exclude=None):
        self.lock.acquire()
        file = self.getValue('configuration')
        if isinstance(file,list):
            file=file[0]
        if file == None:
            file="config.conf"
        file2="tmp.config.%d.conf"%(random.randint(0,65536*256))

        f = open( file2,"w")
        f.write("<configuration>\n")
        for key in self.config.keys():
            if (exclude==None or not exclude.has_key(key)) and key!="verbose" and key!="trace":
                v = self.config[key]
                self.writeKey(f,key,v)

        f.write("</configuration>\n")
        f.close()
        self.lock.release()

        # move the temporary file2 to file
        try:
            shutil.move(file2,file)
        except:
            error("could not move temporary configuration file to " + str(file))

    def writeKey(self,f,key,value):
        if type(value).__name__=='dict':
            f.write("<" + key + " type='hash'>\r\n")
            for k in value.keys():
                writeKey(f,k,value[k])
            f.write("</" + key + ">\r\n")
        elif type(value).__name__=='list':
            f.write("<" + key + " type='list'>\r\n")
            for k in value:
                writeKey(f,None,k)
            f.write("</" + key + ">\r\n")
        else:
            f.write("  <key ")
            if not key == None:
                f.write("id='" + str(key) + "' ")
            f.write("value='"+ str(value) + "'/>\r\n")


    def getValue(self,key):
        if self.config.has_key(key):
            return self.config[key]
        return None

    def setValue(self,key,value):
        self.lock.acquire()
        if value==None and self.config.has_key(key):
            self.config.remove(key)
        elif not value == None:
            self.config[key]=value
        self.lock.release()
        if self.config.has_key("save-on-set") and self.config["save-on-set"]:
            writeConfig()

    def addValue(self,key,value):
        # add a value to a list type configuration setting
        self.lock.acquire()

        if value != None:
            if not self.config.has_key(key):
                self.config[key]=[value]
            else:
                val=self.getValue(key)
                if isinstance(val,list):
                    val.append(value)
                    self.config[key]=val
                else:
                    value=[val,value]
                    self.config[key]=value
        self.lock.release()

def mygetopt(args,options):
    shortlist=""
    longlist=[]
    for k in options.keys():
        if options[k].shortoption!=None:
            o=options[k].shortoption[1:] # skip the dash
            if options[k].hasparameter:
                o+=":"
            shortlist+=o
        if options[k].longoption!=None:
            o=options[k].longoption[2:] # skip the dashes
            if options[k].hasparameter:
                o+="="
            longlist.append(o)

    if sys.version[0] != "2" or ord(sys.version[2]) < ord("3"):
        return getopt.getopt(args, shortlist, longlist)
    else:
        return getopt.gnu_getopt(args, shortlist, longlist)

globals.Config=Configuration()
globals.Config.setOption("configuration",globals.Config.Option("-c","--config","configuration file",["freezer.conf"],True))
globals.Config.setOption("verbose",globals.Config.Option("-v","--verbose","verbose output",0,False))
globals.Config.setOption("trace",globals.Config.Option("-t","--trace","verbose output filter",{},True))
globals.Config.setOption("help",globals.Config.Option("-h","--help","print this help",None,False))



# Module Imports
import os, os.path
import lxml.etree as ET
import pickle
import re
import bacch

# Reader Class
class Reader():
    """ Reads project files and organizes the data and
    provides methods for the builder to operate on.
    """

    def __init__(self, args):
        self.master = args.source
        
        self.namespaces = {
            "bacch": "http://avoceteditors.com/2016/bacch",
            "book": "http://docbook.org/ns/docbook",
	    "xi": "http://www.w3.org/2001/XInclude"
            }
        self.data_base = {
            'content': {},
            'config': {}
            }
        self.data = self.data_base

        # Load Data
        self.load_data(args)

        # Save Data
        self.save_data()

    
    # Pickle Data
    def save_data(self):
        """ Takes the current state of the data varaible
        and serializes it using the pickle module.
        """
        f = open(self.pickle_path, 'wb')
        pickle.dump(self.data, f)
        f.close()

    # Load Pickle
    def load_data(self, args):
        """ Loads the data variable from pickle.  In the
        event that the file is unavailable or any of the
        content has changed since the last update, it
        reloads the relevant data.
        """
        
        self.pickle_path = os.path.join('.bacch', 'bacch.pickle')

        try:
            f = open(self.pickle_path, 'rb')
            self.data = pickle.load(f)
            f.close()

            config = self.data['config']
            if self.check_config(config) or args.sync:
                self.data = self.data_base
                config = self.update_config(args)
                config['args'] = args
                self.update_data(args, config)
            
        except:
            self.data = self.data_base
            config = self.update_config(args)
            config['args'] = args
            self.update_data(args, config)
     
    # Check Configuration
    def check_config(self, config):
        """ Method checks the current state of the 
        configuration data.  If the master.xml file has
        changed since the last run, it updates the config.
        """
        newmtime = os.path.getmtime(self.master)
        try:
            if newmtime > config['mtime']:
                return True
            else:
                return False
        except:
            return True

    # Update Configuration 
    def update_config(self, args):
        """ Method udpates the configuration data.
        """

        # Open Master File
        f = open(self.master, 'rb')
        content = f.read()
        f.close()
        
        mtime = os.path.getmtime(self.master)

        config = {
            "resources": {},
            "prompts": {},
            "books": {},
            'builds': {},
            'mtime': mtime
        } 
 
        doctree = ET.fromstring(content)
        ######################
        # Configuration
        config_data = doctree.xpath('bacch:config', 
                namespaces=self.namespaces)[0]

      
        # Resource
        base = config_data.xpath('bacch:resources/*',
                namespaces=self.namespaces)
        
        if args.wdir is not None:
            wdir = args.wdir
        else:
            wdir = '.'

        for i in base:
            attr = i.attrib
            name = attr['id']
            role = attr['role']
            path = os.path.abspath(name)
            config['resources'][name] = {
                    'role': role,
                    'path': path }


        # Prompt Cofiguration
        base = config_data.xpath('bacch:prompts',
                namespaces = self.namespaces)[0]
        
        for i in base:
            name = i.attrib['id']
            config['prompts'][name] = {
                "PS1": '',
                "PS2": ''
                    }
            for prompt in i.xpath('bacch:ps',
                    namespaces = self.namespaces):
                role = prompt.attrib['role']
                text = prompt.text
                config['prompts'][name]['PS%s' % role] = text
        
        # Build Configuration
        base = config_data.xpath('bacch:builds',
                namespaces = self.namespaces)[0]

        for i in base:
            iattr = i.attrib
            name = iattr['id']
            path = iattr['path']
            typ = iattr['type']
            form = iattr['format']

            config['builds'][name] = {
                'path': path,
                'type': typ,
                'form': form
            }

        # Books
        base = config_data.xpath('bacch:book',
                namespaces = self.namespaces)

        for i in base:
            book_attr = i.attrib

            name = book_attr['id']

            config['books'][name] = {}

        config['ns'] = self.namespaces

        return config
       
    # Update Data
    def update_data(self, args, config):
        """ Method updates the project data.
        """

        resources = config['resources']
        sourcedir = None
        for i in resources:
            check = resources[i]['role']
            if check == 'src' and sourcedir is None:
                sourcedir = resources[i]['path']
            elif check == 'src' and sourcedir is not None:
                raise ValueError("Multiple source directories")

        if sourcedir is None:
            raise ValueError("Unalbe to find source directory")

        base_listdir = os.listdir(sourcedir)
        

        for i in base_listdir:
            (name, ext) = os.path.splitext(i)
            if ext == '.xml':

                try:
                    read = self.data['content'][name]
                    read.check_status()

                except:
                    read = bacch.Entry(args, sourcedir, 
                            config, i, name)
                    read.check_status()
                    self.data['content'][name] = read

        
    # Retrieve Data
    def fetch_data(self):
        """ Retrieves data on project reads for the builder.
        """
        return self.data

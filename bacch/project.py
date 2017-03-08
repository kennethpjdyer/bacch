# Copyright (c) 2017, Kenneth P. J. Dyer <kenneth@avoceteditors.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the name of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
from os.path import exists, isfile, isdir, join
from os import getcwd

# Local Imports
from . import core
from . import xml
from .resource import Resource

# Initialize Logger
from logging import getLogger
logger = getLogger()


####################################
# Project Controller Class
class Project():

    title = "Untitled"
    slogan = None
    default_build = None

    # Initialize Class
    def __init__(self):
        logger.info("Initializing Project")

        self.path = getcwd()

        # Open Project XML File
        doctree = xml.read_xml("project.xml")

        if doctree is None:
            logger.critical("Unable to find or parse project.xml") 
            core.exit(1)

        # Load Project Metadata
        self.load_meta(doctree)

        # Load Project Resources
        self.load_resources(doctree)

        # Load Sectional Data
        self.load_sectdata()

        # Ready
        logger.debug("Project Ready")

    
    # Representation
    def __repr__(self):
        return "<class title='%s'  path='%s'>" % (self.title, slogan, self.path)
    

    # Fetch Metadata
    def load_meta(self, doctree):
        logger.debug("Loading Project Metadata")

        # Fetch Title 
        title = xml.fetch_xpath(doctree, "/bacch:project/book:info/book:title")
        if len(title) > 0:
            self.title = title[0].text

        # Fetch Slogan
        slogan = xml.fetch_xpath(doctree, "/bacch:project/book:info/bacch:slogan")
        if len(slogan) > 0:
            self.slogan = slogan[0].text
        


    # Load Resources
    def load_resources(self, doctree):
        logger.debug("Loading Project Resources")

        self.resources = {}

        # Resource Configuration
        resources = xml.fetch_xpath(doctree, "/bacch:project/bacch:config/bacch:resources/bacch:resource")
        if not len(resources) > 0:
            logger.critical("Unable to locate project resources")
            core.exit(1)
        
        for resource in resources:
            attr = resource.attrib
            try:
                path = join(self.path, attr["path"])
                name = attr["name"]
                typ = attr["type"]
                try:
                    lang = attr["lang"]
                except:
                    lang = "en"

                # Set Default Build
                if typ == "source" or typ == "src":
                    self.default_build = name

                if exists(path) and isdir(path):
                    # Initialize Resource
                    self.resources[name] = Resource(name, path, lang, typ)

            except:
                logger.warning("Document Parse Failed: %s" % name)

    # Retrieve Sectional Data
    def load_sectdata(self):
        self.sectdata = {}
        for key, resource in self.resources.items():
            
            # Fetch Resource Data
            self.sectdata[key] = resource.fetch_sectdata()


    # Retrieve Build Target
    def build_target(self, build):

        # Initialize Target
        target = ()

        if build is None and self.default_build is None:
            logger.critical("Unable to identify build target")
            core.exit(1)

        else:

            # Find Target
            for key, resource in self.resources.items():

                if resource.find_target(build):
                    return (key, build)

            # Build Default 
            if target == (): 
                logger.critical("Need support for default builds")
                core.exit(1)


    # Compile Doctree
    def compile(self, build):
        key = build[0]
        target = build[1]

        # Load Resource
        resource = self.resources[key]

        # Compile Doctree
        doctree = resource.compile(self.resources, target)

        # Return Doctree
        return doctree

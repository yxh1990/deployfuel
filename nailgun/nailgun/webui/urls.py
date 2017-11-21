# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import web, os, wsgiref.util, mimetypes, datetime  

from nailgun.webui.handlers import IndexHandler

urls = (
    r"/", IndexHandler.__name__,
    '/static/(.*)', 'static', 
)

_locals = locals()


def app():
    return web.application(urls, _locals)

def serve_static(filename, mime_type=None):  
  if mime_type is None: 
   mime_type = mimetypes.guess_type(filename)[0]  
   web.header('Content-Type', '%s' % mime_type)  
   stat = os.stat(filename)  
   web.header('Content-Length', '%s' % stat.st_size)  
   web.header('Last-Modified', '%s' %  
   web.http.lastmodified(datetime.datetime.fromtimestamp(stat.st_mtime))) 
   return wsgiref.util.FileWrapper(open(filename, 'rb'), 16384) 


class static(object):   
 def GET(self, name):  
  return serve_static(os.path.join('static', name).replace('\\', '/'))
   
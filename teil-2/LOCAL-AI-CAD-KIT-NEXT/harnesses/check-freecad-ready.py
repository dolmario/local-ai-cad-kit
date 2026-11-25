import json
import sys
import xmlrpc.client

class Transport(xmlrpc.client.Transport):
    def make_connection(self,host):
        connection=super().make_connection(host)
        connection.timeout=12
        return connection

with xmlrpc.client.ServerProxy('http://127.0.0.1:9875',allow_none=True,transport=Transport()) as rpc:
    status=rpc.get_rpc_status()
    assert status.get('success') and status.get('rpc_server')=='running'
    documents=rpc.list_documents()
    assert isinstance(documents,list),'Unexpected document listing response'
print(json.dumps({'rpc_ready':True,'gui_dispatch_verified':True,'documents_before':documents}))

"""Startskript: schaltet in FreeCAD den RPC-Server des MCP-Addons ein (127.0.0.1:9875).

Aufruf: "C:\\Users\\JT\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\freecad.exe" freecad_rpc_start.py
Braucht die Oberfläche (nicht freecadcmd) und das Addon in %APPDATA%\\FreeCAD\\v1-1\\Mod\\FreeCADMCP.
"""
from rpc_server import rpc_server as _bridge

print(_bridge.start_rpc_server())

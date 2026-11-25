import argparse
import copy
import importlib.util
import json
import os
import sys
from pathlib import Path


def cline_transport(kit, argv):
    if os.name != 'nt':
        return {'type': 'stdio', 'command': argv[0], 'args': argv[1:]}
    # Cline Core 0.2.1 invokes MCP through cmd.exe on Windows.
    return {
        'type': 'stdio',
        'command': 'uv',
        'args': ['run', '--offline', '--no-project', '--python', '3.12',
                 'python', '-I', 'cline-stdio.py'],
        'cwd': str(kit / 'harnesses'),
        'env': {'CAD_MCP_ARGV_JSON': json.dumps(argv)},
    }


def configure(kit, runtime, harness, profile, auto=False, web_mode='off', searxng_url=None, freecadcmd=None):
    kit=Path(kit).resolve()
    runtime=Path(runtime).resolve()
    if freecadcmd is not None:
        freecadcmd=Path(freecadcmd).expanduser().resolve()
        if not freecadcmd.is_file():
            raise FileNotFoundError(f'FreeCADCmd executable is missing: {freecadcmd}')
        freecadcmd=str(freecadcmd)
    runtime.mkdir(parents=True,exist_ok=False)
    assert web_mode in ('off','fetch','search')
    spec=importlib.util.spec_from_file_location('cad_skill_learning',Path(__file__).with_name('skill_learning.py'))
    learning_module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learning_module)
    learning=learning_module.prepare(kit,runtime,harness)
    template=(kit/'harnesses/templates'/f'{harness}.json').read_text('utf-8')
    for token,value in [('${KIT}',str(kit)),('${RUNTIME}',str(runtime))]:
        template=template.replace(token,json.dumps(value)[1:-1])
    config=json.loads(template)
    model=profile.get('api_model','local-cad')
    base_url=profile.get('base_url','http://127.0.0.1:18080/v1').rstrip('/')
    context=int(profile.get('context',262144))
    output=int(profile.get('output_tokens',131072))
    vision=profile.get('vision',True)
    assert 0<output<=context
    mcp=['uvx','--offline','--python','3.12','--from','freecad-mcp==0.1.31','freecad-mcp']
    if not vision:
        mcp=['uv','run','--offline','--no-project','--python','3.12','python',str(kit/'harnesses/text-feedback-mcp.py')]
    if freecadcmd is not None:
        mcp+=['--freecadcmd',freecadcmd]
    if harness in ('opencode','opencode2'):
        config['model']='local/'+model
        config['agent']['cad']['model']='local/'+model
        config['provider']['local']['options']['baseURL']=base_url
        definition=config['provider']['local']['models'].pop('local-cad')
        definition['limit']={'context':context,'output':output}
        definition['modalities']['input']=['text','image'] if vision else ['text']
        config['provider']['local']['models']={model:definition}
        servers=config['mcp']['servers'] if harness=='opencode2' else config['mcp']
        servers['freecad']['command']=mcp
        config['skills']={'paths':[learning['skills_dir']]} if harness=='opencode' else [learning['skills_dir']]
        if auto and harness=='opencode':
            config['permission']={'*':'allow','task':'deny'}
            config['agent']['cad']['permission']={'*':'allow','task':'deny'}
        elif harness=='opencode':
            config['permission']['task']='deny'
            config['agent']['cad']['permission']['task']='deny'
        if auto and harness=='opencode2':
            config['permissions']=[{'action':'*','resource':'*','effect':'allow'},{'action':'subagent','resource':'*','effect':'deny'}]
        elif harness=='opencode2':
            config['permissions']=[{'action':'subagent','resource':'*','effect':'deny'}]
    elif harness=='cline-core':
        config['mcpServers']['freecad']['transport']=cline_transport(kit, mcp)
    elif harness=='crush':
        config['providers']['local']['base_url']=base_url
        definition=config['providers']['local']['models'][0]
        definition.update(id=model,context_window=context,default_max_tokens=output)
        definition['capabilities']['vision']=vision
        for definition in config['models'].values():definition.update(model=model,max_tokens=output)
        config['options']['data_directory']=str(runtime/'data')
        config['options']['skills_paths']=[learning['skills_dir']]
        config['mcp']['freecad'].update(command=mcp[0],args=mcp[1:])
    elif harness=='hermes':
        config['model'].update(default=model,base_url=base_url,context_length=context)
        config['terminal']['cwd']=str(kit)
        config['mcp_servers']['freecad'].update(command=mcp[0],args=mcp[1:])
        if vision:config['auxiliary']['vision'].update(model=model,base_url=base_url)
        else:config.pop('auxiliary',None)
        config['skills']={**config.get('skills',{}),**learning['hermes']}
    web_command=None
    if web_mode!='off':
        web_command=[sys.executable,'-u',str(kit/'harnesses/web-tools.py'),'--mode',web_mode,
                     '--evidence-dir',str(runtime/'web-evidence')]
        if searxng_url:web_command+=['--searxng-url',searxng_url]
        if harness in ('opencode','opencode2'):
            servers['cad_web']=copy.deepcopy(servers['freecad'])
            servers['cad_web']['command']=web_command
        elif harness=='cline-core':
            config['mcpServers']['cad_web']=copy.deepcopy(config['mcpServers']['freecad'])
            config['mcpServers']['cad_web']['transport']=cline_transport(kit, web_command)
        elif harness=='crush':
            config['mcp']['cad_web']=copy.deepcopy(config['mcp']['freecad'])
            config['mcp']['cad_web'].update(command=web_command[0],args=web_command[1:])
        elif harness=='hermes':
            config['mcp_servers']['cad_web']=copy.deepcopy(config['mcp_servers']['freecad'])
            config['mcp_servers']['cad_web'].update(command=web_command[0],args=web_command[1:])
    config_path=runtime/('config.yaml' if harness=='hermes' else 'config.json')
    config_path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    profile_path=runtime/'profile.json'
    profile_path.write_text(json.dumps(profile,indent=2),encoding='utf-8')
    return {'config':str(config_path),'runtime':str(runtime),'kit':str(kit),'harness':harness,
            'base_url':base_url,'api_model':model,'context':context,'output_tokens':output,
            'vision':vision,'auto_approve':auto,'skills_dir':learning['skills_dir'],
            'freecadcmd':freecadcmd,
            'learning_instructions':learning['instructions'],'skill_learning':learning,
            'web_mode':web_mode,'web_command':web_command,
            'web_evidence_dir':str(runtime/'web-evidence') if web_mode!='off' else None,
            'hermes_web_toolset':'mcp-cad_web' if web_mode!='off' else None}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('kit')
    parser.add_argument('runtime')
    parser.add_argument('harness',choices=['opencode','opencode2','cline-core','crush','hermes'])
    parser.add_argument('profile')
    parser.add_argument('--auto',action='store_true')
    parser.add_argument('--web-mode',choices=['off','fetch','search'],default='off')
    parser.add_argument('--searxng-url')
    parser.add_argument('--freecadcmd')
    args=parser.parse_args()
    profile=json.loads(Path(args.profile).read_text('utf-8-sig'))
    print(json.dumps(configure(args.kit,args.runtime,args.harness,profile,args.auto,args.web_mode,args.searxng_url,args.freecadcmd)))

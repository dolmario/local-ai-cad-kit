import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createMcpImageHooks} from './mcp-image-bridge.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const [runtime,promptPath]=process.argv.slice(2);
if(!runtime||!promptPath)throw new Error('Expected runtime directory and prompt file');
const profile=JSON.parse(await fs.readFile(path.join(runtime,'profile.json'),'utf8'));
const {ClineCore,getClineDefaultSystemPrompt}=await import(pathToFileURL(path.join(root,'programs/harnesses/cline-core/node_modules/@cline/sdk/dist/index.js')).href);
const core=await ClineCore.create({clientName:'local-ai-cad-kit',backendMode:'local',automation:false});
const unsubscribe=core.subscribe(event=>process.stdout.write(JSON.stringify({type:'agent_event',event})+'\n'));
const vision=profile.vision!==false;
const model=profile.api_model??'local-cad';
const context=profile.context??262144;
const output=profile.output_tokens??131072;
try{
  const started=await core.start({config:{
    cwd:root,workspaceRoot:root,providerId:'openai-compatible',modelId:model,
    apiKey:process.env.LOCAL_CAD_API_KEY??'local-test-no-secret',
    baseUrl:profile.base_url??'http://127.0.0.1:18080/v1',maxTokensPerTurn:output,maxIterations:256,
    knownModels:{[model]:{id:model,name:'Local CAD',contextWindow:context,maxInputTokens:context,maxTokens:output,
      capabilities:['tools','streaming','reasoning',...(vision?['images']:[])],modalities:{input:vision?['text','image']:['text'],output:['text']}}},
    thinking:true,reasoningEffort:'xhigh',thinkingBudgetTokens:profile.thinking_budget<0?output:(profile.thinking_budget??output),
    systemPrompt:getClineDefaultSystemPrompt({rootPath:root,cwd:root,mode:'yolo',providerId:'openai-compatible'}),
    enableTools:true,enableSpawnAgent:false,enableAgentTeams:false,yolo:true,
    compaction:{enabled:false},checkpoint:{enabled:false},hooks:createMcpImageHooks()
  },interactive:false,mode:'yolo'});
  await fs.writeFile(path.join(runtime,'session.json'),JSON.stringify(started,null,2));
  const prompt=await fs.readFile(promptPath,'utf8');
  const result=await core.send({sessionId:started.sessionId,prompt,mode:'yolo',timeoutMs:10800000});
  await fs.writeFile(path.join(runtime,'result.json'),JSON.stringify(result,null,2));
  if(result.finishReason!=='completed')throw new Error('Cline Core task ended with '+result.finishReason+'; inspect result.json before continuing');
}finally{unsubscribe();await core.dispose();}

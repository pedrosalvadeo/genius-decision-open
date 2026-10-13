#!/usr/bin/env node
// Independent malicious-peer tests. Imports public consumer, never server/Kernel.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {GeniusClient} from '../consumer/client.mjs';
import {byteEnvelope,decodeEnvelope,strictJSON} from '../consumer/bytes.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const out=resolve(root,process.argv[2]??'validation/audit_runs/AUDIT_CONSUMER_DRAFT_01');
await mkdir(out,{recursive:false});
const hash=b=>createHash('sha256').update(b).digest('hex');
const files=['protocols/tests/audit_consumer.mjs','protocols/CONTRACT.md','protocols/AUDIT_DESIGN_F4.md',
  ...['bytes','client','transport','package','cli'].map(n=>`protocols/consumer/${n}.mjs`)];
async function hashes(){return Object.fromEntries(await Promise.all(files.map(async f=>[f,hash(await readFile(join(root,f)))])))}
const before=await hashes();
const caps={protocol_version:'genius-protocols/1.0',protocols_version:'GENIUS-PROTOCOLS-1.0.0',kernel_version:'GENIUS-KERNEL-1.0.1',specification:'GENIUS-SPEC-1.0.0',theory_snapshot:'GENIUS-THEORY-2026-09-23-S2',profile:'FP1_FINITE_EXACT',input_format:'genius-fp1/1.0',result_format:'genius-fp1-result/1.0',capabilities:['evaluate','verify_result','verify_certificate'],transport_limits:{max_frame_bytes:'16777216',max_input_bytes:'2097152',max_candidate_bytes:'8388608',max_response_bytes:'33554432',max_batch_items:'16',max_limit_digits:'12'},default_kernel_limits:{},allowed_kernel_limits:['max_nodes','max_operations','max_seconds','max_input_bytes','max_integer_digits'],environment:{python_recursion_depth:'1000'},cancellation:'PROCESS_TERMINATION_ONLY'};
const input=Buffer.from('{"synthetic":"consumer audit bytes"}\n');
const errorResult={format:'genius-fp1-result/1.0',input_digest:hash(input),specification:'GENIUS-SPEC-1.0.0',execution:{status:'ERROR',limits:[],progress:{completed_policies:[],expanded_nodes:'0'}},presentation:'UNRESOLVED',diagnostics:[],checks:[],policies:[],decision:{state:'BLOCKED',reasons:['diagnostic']},integration:{state:'BLOCKED',reasons:['diagnostic']}};
// This fixture is only for consumer transport-shape validation. No claim is
// made that its empty diagnostic table constitutes a verified Kernel Result.
const unit={input:byteEnvelope(input),result:byteEnvelope(Buffer.from(JSON.stringify(errorResult)))};
const cases=[];
async function trial(id,fn){const checks=[];const check=(label,actual,expected)=>checks.push({label,actual,expected,pass:JSON.stringify(actual)===JSON.stringify(expected)});let error=null;try{await fn(check)}catch(e){error=e.stack};const item={id,status:error?'ERROR':checks.every(c=>c.pass)?'PASS':'FAIL',checks,error};cases.push(item);await writeFile(join(out,id+'.json'),JSON.stringify(item,null,2)+'\n');console.log(id,item.status)}
async function peer(test,check){
 const setting={caps:structuredClone(caps),unit:structuredClone(unit),...test};
 const code=`const setting=${JSON.stringify(setting)};let buffer='';let count=0;process.stdin.on('data',chunk=>{buffer+=chunk;for(;;){const at=buffer.indexOf('\\n');if(at<0)break;const request=JSON.parse(buffer.slice(0,at));buffer=buffer.slice(at+1);count++;if(setting.pauseAfterInit&&count>1)return;let response={jsonrpc:'2.0',id:request.id,result:count===1?setting.caps:setting.unit};if(setting.badID)response.id='foreign';let raw=JSON.stringify(response);if(setting.duplicate)raw=raw.replace('"jsonrpc":"2.0"','"jsonrpc":"2.0","jsonrpc":"2.0"');if(setting.utf8){process.stdout.write(Buffer.from([255,10]));continue;}if(setting.truncate){process.stdout.write(raw);process.exit(0);}process.stdout.write(raw+'\\n');}});process.stdin.on('end',()=>process.exit(0));`;
 const frames=[];const controller=new AbortController();
 const client=new GeniusClient({command:process.execPath,args:['-e',code],cwd:root,timeoutMs:test.timeoutMs??2000,onFrame:(direction,frame)=>{frames.push({direction,frame:frame.toString('base64')});if(test.cancel&&direction==='send'&&frames.filter(x=>x.direction==='send').length===2)controller.abort();}});
 let outcome;
 try{await client.initialize();if(!test.initializeOnly){const exchange=await client.evaluate(input,{signal:controller.signal,timeoutMs:test.replyTimeoutMs});outcome={success:true,execution:exchange.result.execution.status}}else outcome={success:true}}
 catch(e){outcome={success:false,code:e.code??e.name}}
 finally{await client.close()}
 check('expected success',outcome.success,test.success??false);
 if(test.code)check('expected failure category',outcome.code,test.code);
 if(test.maximumSends)check('no instance after failed negotiation',frames.filter(f=>f.direction==='send').length<=test.maximumSends,true);
 if(test.expectedSends)check('pending operation after successful negotiation',frames.filter(f=>f.direction==='send').length,test.expectedSends);
 check('session subprocess ended',client.transport.child.exitCode!==null||client.transport.child.signalCode!==null,true);
 await writeFile(join(out,test.id+'-frames.json'),JSON.stringify({outcome,frames},null,2)+'\n');
}
await trial('AUD4-CON-001',async check=>{for(const size of [0,1,2,1000000,2097152]){const b=Buffer.alloc(size,32);check('valid base64 size '+size,decodeEnvelope(byteEnvelope(b),'2097152').equals(b),true)}for(const data of ['e31=','e30','e30=\n','e30_']){let rejected=false;try{decodeEnvelope({encoding:'base64',data,sha256:hash(Buffer.from('{}'))},'2097152')}catch{rejected=true}check('invalid base64 '+JSON.stringify(data),rejected,true)}});
await trial('AUD4-CON-002',async check=>{for(const raw of [Buffer.from('{"a":1,"\\u0061":2}'),Buffer.from('"\\ud800"'),Buffer.from([255]),Buffer.from([239,187,191,123,125]),Buffer.from('{"x":9007199254740993}')]){let rejected=false;try{strictJSON(raw)}catch{rejected=true}check('invalid parser bytes '+hash(raw),rejected,true)}check('valid surrogate pair',strictJSON(Buffer.from('"\\ud834\\udd1e"')),'𝄞');check('preserved decomposed scalar',strictJSON(Buffer.from('"e\\u0301"')),'e\u0301')});
await trial('AUD4-CON-003',check=>peer({id:'AUD4-CON-003',success:true},check));
for(const [i,key,value] of [[4,'kernel_version','GENIUS-KERNEL-9.0.0'],[5,'protocol_version','genius-protocols/9.0'],[6,'capabilities',['evaluate']]]){
 const info=structuredClone(caps);info[key]=value;const id='AUD4-CON-'+String(i).padStart(3,'0');await trial(id,check=>peer({id,caps:info,maximumSends:1,code:'PROTOCOL_VIOLATION'},check));
}
const wrongEcho=structuredClone(unit);wrongEcho.input=byteEnvelope(Buffer.from('{}'));
await trial('AUD4-CON-007',check=>peer({id:'AUD4-CON-007',unit:wrongEcho,code:'PROTOCOL_VIOLATION'},check));
const wrongDigest=structuredClone(unit);wrongDigest.result.sha256='0'.repeat(64);
await trial('AUD4-CON-008',check=>peer({id:'AUD4-CON-008',unit:wrongDigest,code:'PROTOCOL_VIOLATION'},check));
const wrongResult=structuredClone(errorResult);wrongResult.input_digest='0'.repeat(64);const wrongBinding={...unit,result:byteEnvelope(Buffer.from(JSON.stringify(wrongResult)))};
await trial('AUD4-CON-009',check=>peer({id:'AUD4-CON-009',unit:wrongBinding,code:'PROTOCOL_VIOLATION'},check));
await trial('AUD4-CON-010',check=>peer({id:'AUD4-CON-010',duplicate:true,code:'PROTOCOL_VIOLATION'},check));
await trial('AUD4-CON-011',check=>peer({id:'AUD4-CON-011',badID:true,code:'PROTOCOL_VIOLATION'},check));
await trial('AUD4-CON-012',check=>peer({id:'AUD4-CON-012',utf8:true,code:'PROTOCOL_VIOLATION'},check));
await trial('AUD4-CON-013',check=>peer({id:'AUD4-CON-013',truncate:true,code:'TRANSPORT_CLOSED'},check));
await trial('AUD4-CON-014',check=>peer({id:'AUD4-CON-014',pauseAfterInit:true,cancel:true,expectedSends:2,code:'CANCELLED'},check));
await trial('AUD4-CON-015',check=>peer({id:'AUD4-CON-015',pauseAfterInit:true,replyTimeoutMs:50,expectedSends:2,code:'TRANSPORT_TIMEOUT'},check));
// AUD4-CON-016 preregistered after author R03: a caller overwrites both
// Buffers during the pending verify. Returned snapshots must match the bytes
// encoded at invocation, not the later caller memory. Peer is transport-only.
await trial('AUD4-CON-016',async check=>{
 const mutableInput=Buffer.from(input),candidate=Buffer.from('{"candidate":"original"}');
 const inputHash=hash(mutableInput),candidateHash=hash(candidate);
 const code=`const caps=${JSON.stringify(caps)};let buffer='';process.stdin.on('data',chunk=>{buffer+=chunk;let at;while((at=buffer.indexOf('\\n'))>=0){const r=JSON.parse(buffer.slice(0,at));buffer=buffer.slice(at+1);const result=r.method==='genius.initialize'?caps:{input_digest:r.params.input.sha256,artifact_digest:r.params.candidate.sha256,report:{valid:false,status:'INVALID',errors:['MOCK_REJECTION']}};setTimeout(()=>process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:r.id,result})+'\\n'),10)}});process.stdin.on('end',()=>process.exit(0));`;
 const client=new GeniusClient({command:process.execPath,args:['-e',code],timeoutMs:2000});
 try{await client.initialize();const pending=client.verifyResult(mutableInput,candidate);mutableInput.fill(120);candidate.fill(121);const exchange=await pending;
 check('returned input snapshot',hash(exchange.inputBytes),inputHash);check('returned candidate snapshot',hash(exchange.candidateBytes),candidateHash);
 check('input digest binding',exchange.inputDigest,inputHash);check('artifact digest binding',exchange.artifactDigest,candidateHash);
 }finally{await client.close()}
});
const after=await hashes();const report={status:cases.every(c=>c.status==='PASS')&&JSON.stringify(before)===JSON.stringify(after)?'PASS':'FAIL',cases:cases.length,checks:cases.reduce((n,c)=>n+c.checks.length,0),source_before:before,source_after:after,sources_unchanged:JSON.stringify(before)===JSON.stringify(after),node:process.version,scope:'Independent consumer public-interface tests with synthetic local malicious peer; not Kernel verification or general second verifier.',results:cases.map(({id,status})=>({id,status}))};await writeFile(join(out,'REPORT.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));process.exitCode=report.status==='PASS'?0:1;

import {beforeEach,afterEach,it,vi,expect} from 'vitest';
import {saveDailyNote,unsaveDailyNote,listSavedNotes} from './client';
import {enqueueSavedNoteMutation} from '../storage/savedNoteMutationQueue';
import {testLocks} from '../session/testLocks';
beforeEach(()=>{
 localStorage.clear();sessionStorage.clear();sessionStorage.setItem('la-lanh-session-epoch','epoch-a');
 document.cookie='la_lanh_csrf=synthetic; path=/';
 vi.stubGlobal('navigator',Object.create(navigator,{locks:{value:testLocks(),configurable:true}}));
});
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();document.cookie='la_lanh_csrf=; Max-Age=0; path=/';});
it('an acknowledged unsave is not reversed by an older queued save on the next saved-list refresh',async()=>{
 enqueueSavedNoteMutation({sessionEpoch:'epoch-a',dailyNoteId:'note-a',revisionId:'revision-a',intent:'save'});
 const methods:string[]=[];
 vi.spyOn(globalThis,'fetch').mockImplementation((_url,init)=>{
  methods.push(init?.method??'GET');
  return Promise.resolve(init?.method==='DELETE'?new Response(null,{status:204}):new Response(JSON.stringify(init?.method==='PUT'?{daily_note_id:'note-a'}:[]),{status:200,headers:{'Content-Type':'application/json'}}));
 });
 await unsaveDailyNote('note-a','revision-a'); // server ACK of deliberate deletion
 await listSavedNotes(); // normal UI invalidation calls this
 expect(methods).toEqual(['DELETE','GET']);
});
it('an acknowledged save is not reversed by an older queued unsave on the next saved-list refresh',async()=>{
 enqueueSavedNoteMutation({sessionEpoch:'epoch-a',dailyNoteId:'note-a',revisionId:'revision-a',intent:'unsave'});
 const methods:string[]=[];
 vi.spyOn(globalThis,'fetch').mockImplementation((_url,init)=>{
  methods.push(init?.method??'GET');
  return Promise.resolve(init?.method==='DELETE'?new Response(null,{status:204}):new Response(JSON.stringify(init?.method==='PUT'?{daily_note_id:'note-a'}:[]),{status:200,headers:{'Content-Type':'application/json'}}));
 });
 await saveDailyNote('note-a','revision-a');
 await listSavedNotes();
 expect(methods).toEqual(['PUT','GET']);
});
// Codex #48 @ 2d5636b: an older call that fails after a newer call's ACK must not queue a retry.
function raceFetch(methods:string[]){
 const pending:{method:string;fail:()=>void}[]=[];
 vi.spyOn(globalThis,'fetch').mockImplementation((_url,init)=>{
  const method=init?.method??'GET';methods.push(method);
  if(method==='GET')return Promise.resolve(new Response('[]',{status:200,headers:{'Content-Type':'application/json'}}));
  if(pending.length===0&&methods.filter(m=>m!=='GET').length===1){
   return new Promise<Response>((_resolve,reject)=>{pending.push({method,fail:()=>reject(new TypeError('Failed to fetch'))});});
  }
  return Promise.resolve(method==='DELETE'?new Response(null,{status:204}):new Response(JSON.stringify({daily_note_id:'note-a'}),{status:200,headers:{'Content-Type':'application/json'}}));
 });
 return pending;
}
it('an older save failing after a newer unsave ACK does not re-save the note',async()=>{
 const methods:string[]=[];const pending=raceFetch(methods);
 const older=saveDailyNote('note-a','revision-a').catch(()=>undefined);
 await vi.waitFor(()=>expect(pending).toHaveLength(1));
 await unsaveDailyNote('note-a','revision-a');
 pending[0].fail();await older;
 await listSavedNotes();
 expect(methods).toEqual(['PUT','DELETE','GET']);
});
it('an older unsave failing after a newer save ACK does not delete the note',async()=>{
 const methods:string[]=[];const pending=raceFetch(methods);
 const older=unsaveDailyNote('note-a','revision-a');
 await vi.waitFor(()=>expect(pending).toHaveLength(1));
 await saveDailyNote('note-a','revision-a');
 pending[0].fail();await older;
 await listSavedNotes();
 expect(methods).toEqual(['DELETE','PUT','GET']);
});
it('a failed call with no newer ACK still queues its retry',async()=>{
 const methods:string[]=[];const pending=raceFetch(methods);
 const only=saveDailyNote('note-a','revision-a').catch(()=>undefined);
 await vi.waitFor(()=>expect(pending).toHaveLength(1));
 pending[0].fail();await only;
 await listSavedNotes();
 expect(methods).toEqual(['PUT','PUT','GET']);
});

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

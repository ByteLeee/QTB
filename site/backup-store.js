(function(root){
'use strict';
// localStorage writes are atomic per key. Save the recovery copy before replacing
// the live key; a failed snapshot or live write must never become a UI success.
function replace(storage,key,current,next,kind='import'){
 const recovery=key+(kind==='restore'?'-before-restore':'-before-import');
 storage.setItem(recovery,JSON.stringify(current));
 storage.setItem(key,JSON.stringify(next));
 return next;
}
function read(storage,key,kind='import'){
 const raw=storage.getItem(key+(kind==='restore'?'-before-restore':'-before-import'));
 return raw?JSON.parse(raw):null;
}
const api={replace,read};root.QTBBackupStore=api;
if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);

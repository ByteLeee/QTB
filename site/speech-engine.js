(function(root){'use strict';
function create({synth,Utterance,items,onState=()=>{},onPosition=()=>{},setTimer=setTimeout,clearTimer=clearTimeout}){
 let index=0,mode='stopped',token=0,rate=1,voice='',timer=null,sleep=0,pending=false;
 function emit(message){onState({mode,index,total:items.length,message});}
 function stop(message='朗读已停止。'){token++;pending=false;mode='stopped';synth.cancel();if(timer)clearTimer(timer);timer=null;emit(message);}
 function speak(){if(mode!=='playing')return;if(index>=items.length){stop('本期朗读结束，可以休息或留下回答。');return;}const run=++token,u=new Utterance(items[index].text);u.lang='zh-CN';u.rate=rate;
 const voices=synth.getVoices();u.voice=voices.find(v=>v.voiceURI===voice)||voices.find(v=>/^zh[-_]CN|^cmn/i.test(v.lang))||voices.find(v=>/^zh/i.test(v.lang))||null;
 u.onstart=()=>{if(run===token&&mode!=='stopped')onPosition(index);};u.onend=()=>{if(run!==token||mode==='stopped')return;index++;if(mode==='playing')speak();else pending=true;};u.onerror=e=>{if(run!==token)return;stop('语音未能播放（'+e.error+'）。请换用系统浏览器或其他中文声音后重试。');};emit('正在朗读第 '+(index+1)+' / '+items.length+' 段');synth.speak(u);}
 function start(at=0){stop();if(!items.length){emit('本期没有可朗读的正文。');return;}index=Math.max(0,Math.min(items.length-1,at));mode='playing';if(sleep)timer=setTimer(()=>stop('定时停止已到，休息一下吧。'),sleep*60000);speak();}
 function pause(){if(mode==='playing'){mode='paused';synth.pause();emit('已暂停。');}else if(mode==='paused'){mode='playing';if(pending){pending=false;speak();}else synth.resume();emit('继续朗读。');}}
 function jump(delta){start(index+delta);}
 function preferences(next){rate=next.rate||1;voice=next.voice||'';sleep=next.sleep||0;if(mode==='playing'||mode==='paused')start(index);}
 return {start,pause,stop,jump,preferences,getState:()=>({index,mode})};
}
root.QTBSpeech={create};if(typeof module!=='undefined')module.exports={create};
})(typeof window==='undefined'?globalThis:window);
